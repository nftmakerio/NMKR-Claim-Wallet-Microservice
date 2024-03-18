from flask import Blueprint, request, jsonify, abort, redirect
import requests
from config import BEARER_TOKEN, nmkr_studio_user_id   
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import secrets
from mongo_connector import create_connect_mongodb
from email_sender import send_email
from flask_cors import cross_origin

# Create a Blueprint for the wallet-related routes
wallet_bp = Blueprint('wallet', __name__)


def check_if_wallet_exists(wallet_name):
    headers = {'Authorization': 'Bearer ' + BEARER_TOKEN}
    url = f'https://studio-api.nmkr.io/v2/ListAllWallets/{nmkr_studio_user_id}'
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        wallets = response.json()
        for wallet in wallets:
            if wallet.get('walletName', '').lower() == wallet_name.lower():
                return wallet.get('address')
    return False


@wallet_bp.route('/CreateWallet', methods=['POST'])
@cross_origin()
def create_wallet():
    # Check if necessary data is present
    if not request.form['wallet_does_not_exist_password']:
        abort(400, description="Missing wallet password")

    # TODO: Check if die codes abgelaufen sind
        
    data = {
    'walletpassword': request.form['wallet_does_not_exist_password'],
    "enterpriseaddress": False,
    "walletname": request.form['wallet_does_not_exist_email_hidden']
    }

    print(data)

    response = requests.post(
         'https://studio-api.nmkr.io/v2/CreateWallet/' + nmkr_studio_user_id,
         json=data,
         headers={'Authorization': 'Bearer ' + BEARER_TOKEN}
    )

    print(response)
    json_res = response.json()

    # TODO: Send Passphrase here via email response['seedPhrase']

    # Return the mock response
    return redirect("https://www.nmkr.io/wallet/details?address=" + json_res['address'], code=302)


def generate_magic_link(email, does_wallet_exist):
    db = create_connect_mongodb()
    links_collection = db.magic_links

    # Generate a unique code
    unique_code = secrets.token_urlsafe(16)
    expiry_time = datetime.now() + timedelta(minutes=6000)

    # Insert the code into MongoDB with an expiry time
    link_id = links_collection.insert_one({
        'email': email,
        'code': unique_code,
        'expiry': expiry_time
    }).inserted_id

    # Construct the magic link
    magic_link = f'https://nmkr.io/wallet/signup?code={unique_code}&id={link_id}&does_wallet_exist={does_wallet_exist}&email={email}'

    return magic_link

def generate_magic_link_with_coupon(email, coupon_code):
    db = create_connect_mongodb()
    links_collection = db.magic_links

    # Generate a unique code
    unique_code = secrets.token_urlsafe(16)
    expiry_time = datetime.now() + timedelta(minutes=60)

    # Insert the code into MongoDB with an expiry time
    link_id = links_collection.insert_one({
        'email': email,
        'code': unique_code,
        'expiry': expiry_time
    }).inserted_id

    # Construct the magic link
    magic_link = f'https://nmkr.io/wallet/signup?code={unique_code}&id={link_id}&coupon={coupon_code}&email={email}'

    return magic_link


@wallet_bp.route('/create_login_magic_link', methods=['POST'])
@cross_origin()
def create_magic_link():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    does_wallet_exist = check_if_wallet_exists(email)

    if does_wallet_exist:
        magic_link = generate_magic_link(email, True)
    else:
        magic_link = generate_magic_link(email, False)

    print(magic_link)
    send_email(email, magic_link)

    return jsonify({'message': 'Magic link sent successfully.'}), 200

@wallet_bp.route('/verify_magic_link', methods=['GET'])
def verify_magic_link():
    db = create_connect_mongodb()
    links_collection = db.magic_links

    # Extract code and ID from the query parameters
    code = request.args.get('code')
    link_id = request.args.get('id')

    if not code or not link_id:
        return jsonify({'error': 'Missing code or link ID'}), 400

    # Convert link_id from string to ObjectId for MongoDB query
    try:
        object_id = ObjectId(link_id)
    except:
        return jsonify({'error': 'Invalid link ID format'}), 400

    # Query the database to find the link
    link = links_collection.find_one({'_id': object_id, 'code': code})

    # Check if link exists and has not expired
    if link and link.get('expiry') > datetime.now():
        return jsonify({'message': 'Magic link is valid.'}), 200
    else:
        return jsonify({'error': 'Magic link is invalid or has expired'}), 404
