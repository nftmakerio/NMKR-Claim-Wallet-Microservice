from flask import Blueprint, request, jsonify, abort
import requests
from config import BEARER_TOKEN, nmkr_studio_user_id   
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from datetime import datetime, timedelta
import secrets
from mongo_connector import create_connect_mongodb
from email_sender import send_email

# Create a Blueprint for the wallet-related routes
wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/CreateWallet', methods=['POST'])
def create_wallet():
    # Extract JSON body from the request
    request_data = request.get_json()

    print(request_data)

    # Check if necessary data is present
    if not request_data or 'walletpassword' not in request_data:
        abort(400, description="Missing wallet password")

    data = {
    'walletpassword': request_data['walletpassword'],
    "enterpriseaddress": False,
    "walletname": request_data['email']
    }

    print(data)

    response = requests.post(
         'https://studio-api.nmkr.io/v2/CreateWallet/' + nmkr_studio_user_id,
         json=data,
         headers={'Authorization': 'Bearer ' + BEARER_TOKEN}
    )

    print(response)

    # Return the mock response
    return response.json()


def generate_magic_link(email):
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
    magic_link = f'https://nmkr.io/wallet?code={unique_code}&id={link_id}'

    return magic_link

def generate_magic_link(email, coupon_code):
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
    magic_link = f'https://nmkr.io/wallet?code={unique_code}&id={link_id}&coupon={coupon_code}&email={email}'

    return magic_link


@wallet_bp.route('/create_login_magic_link', methods=['POST'])
def create_magic_link():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    magic_link = generate_magic_link(email)
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
