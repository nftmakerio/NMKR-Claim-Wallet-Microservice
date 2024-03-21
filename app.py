from flask import Flask, request, jsonify, redirect
from pymongo import MongoClient, ReturnDocument
from config import username, password
from coupon_generator import generate_multiple_coupon_codes, generate_coupon_code
from nmkr_api import mint_and_send_random
from flask_cors import CORS, cross_origin
from datetime import timedelta
from multiprocessing import Pool # for the multithreading
from wallet_routes import wallet_bp  # Import the Blueprint
from mongo_connector import create_connect_mongodb
import random
from email_sender import send_email
from wallet_routes import generate_magic_link, generate_magic_link_with_coupon

app = Flask(__name__)

app.register_blueprint(wallet_bp, url_prefix='/')  # Register the Blueprint

CORS(app)


@app.route('/create_coupons', methods=['POST'])
def create_coupons():
    db = create_connect_mongodb()
    coupons_collection = db.coupons

    coupon_codes = request.json.get('coupon_codes')
    project_id = request.json.get('project_id')

    if not coupon_codes or not isinstance(coupon_codes, list) or not project_id:
        return jsonify({"message": "Invalid input"}), 400

    # Each coupon will be associated with a project_id
    coupons = [{"code": code, "state": "unused", "project_id": project_id} for code in coupon_codes]
    coupons_collection.insert_many(coupons)

    return jsonify({"message": "Coupons created successfully"}), 200

@app.route('/use_coupon', methods=['POST'])
def use_coupon():
    db = create_connect_mongodb()
    coupons_collection = db.coupons

    coupon_code = request.json.get('coupon_code')
    wallet_address = request.json.get('wallet_address')

    if not coupon_code or not wallet_address:
        return jsonify({"message": "Coupon code and wallet address required"}), 400

    # Fetch coupon to ensure it's unused and to retrieve its associated project_id
    coupon = coupons_collection.find_one({"code": coupon_code, "state": "unused"})
    if not coupon:
        return jsonify({"message": "Coupon not found or already used"}), 404

    # Use the coupon (mark as "used")
    coupons_collection.update_one({"_id": coupon["_id"]}, {"$set": {"state": "used"}})

    # Call the external API to mint and send using the project_id from the coupon
    api_response = mint_and_send_random(coupon["project_id"], wallet_address)
    # You might want to handle the api_response, for this example, we'll assume a 200 response means success.
    if api_response.status_code == 200:
        return jsonify({"message": "Coupon used and item minted successfully"}), 200
    else:
        return jsonify({"message": "Failed to mint item. Please try again."}), 500

# TEMPORARY
@app.route('/send_emurgo_nft', methods=['POST'])
def send_emurgo_nft():
    wallet_address = request.json.get('wallet_address')

    api_response = mint_and_send_random('9523d6d2-0ff6-4fe7-9d78-3ef2ca1e9d6f', wallet_address)
    # You might want to handle the api_response, for this example, we'll assume a 200 response means success.
    if api_response.status_code == 200:
        return jsonify({"message": "Coupon used and item minted successfully"}), 200
    else:
        return jsonify({"message": "Failed to mint item. Please try again."}), 500



@app.route('/list_coupons', methods=['GET'])
def list_coupons():
    db = create_connect_mongodb()
    coupons_collection = db.coupons

    project_id = request.args.get('project_id')

    # If project_id is provided, filter the coupons by project_id
    if project_id:
        coupons = list(coupons_collection.find({"project_id": project_id}))
    else:
        coupons = list(coupons_collection.find())

    # Convert MongoDB objects to a format that's JSON serializable
    for coupon in coupons:
        coupon["_id"] = str(coupon["_id"])

    return jsonify(coupons), 200

@app.route('/generate_coupons', methods=['POST'])
def generate_coupons():
    request_data = request.get_json()

    print(request_data)

    db = create_connect_mongodb()
    coupons_collection = db.coupons

    print(request_data)

    num_coupons = request_data['num_coupons']
    project_id =  request_data['project_id']

    print(num_coupons)
    if not num_coupons or not project_id:
        return jsonify({"message": "Number of coupons and project ID required"}), 400

    # Generate the coupon codes
    coupon_codes = [generate_coupon_code() for _ in range(num_coupons)]
    print(coupon_codes)
    # Associate each coupon with a project_id
    coupons = [{"code": code, "state": "unused", "project_id": project_id} for code in coupon_codes]
    coupons_collection.insert_many(coupons)

    # Return the generated coupon codes in the response
    return jsonify({"coupon_codes": coupon_codes}), 200

@app.route('/create_project', methods=['POST'])
def create_project_endpoint():
    title = request.json.get('title')
    description = request.json.get('description')
    image_url = request.json.get('image_url')
    project_id = request.json.get('project_id')

    if not all([title, description, image_url, project_id]):
        return jsonify({"message": "All fields (title, description, image_url, project_id) are required"}), 400

    create_project(title, description, image_url, project_id)
    return jsonify({"message": "Project created successfully"}), 200

@app.route('/get_project/<project_id>', methods=['GET'])
@cross_origin()
def get_project_endpoint(project_id):
    project = get_project(project_id)

    if not project:
        return jsonify({"message": "Project not found"}), 404

    return jsonify(project), 200

@app.route('/send_confirmation_mail', methods=['POST'])
@cross_origin()
def send_confirmation_mail():
    # Extract JSON body from the request

    confirmation_email = request.form['confirmation_mail']
    cardano_wallet_address = request.form['cardano_address-2']

    #project_id =  request.form['project_id'] #TODO  Project ID implementieren
    print(confirmation_email)

    # Note: Hardcoded for Emurgo Jakarta, remove afterwards.
    coupon = reserve_random_coupon("9523d6d2-0ff6-4fe7-9d78-3ef2ca1e9d6f")
    #coupon = reserve_random_coupon(project_id)

    if coupon == 500:
        return jsonify({"message": "Internal server error"}), 500
    
    print(coupon)

    if (cardano_wallet_address != ""):
        magic_link = f'https://padierfind.pythonanywhere.com/mintandsend?code=' + coupon + '&wallet_address=' + cardano_wallet_address
    else:
        magic_link = generate_magic_link_with_coupon(confirmation_email, coupon)

    # Send the email
    send_email(confirmation_email, magic_link)

    return redirect("https://www.nmkr.io/claim-success")

def reserve_random_coupon(project_id):
    db = create_connect_mongodb()
    coupons_collection = db.coupons

    # Find all unused coupons for a specific project_id
    unused_coupons = list(coupons_collection.find({"state": "unused", "project_id": project_id}))

    if not unused_coupons:
        return {"message": "No unused coupons available for this project"}, 404

    # Select a random coupon from the list of unused coupons
    random_coupon = random.choice(unused_coupons)

    # Update the selected coupon's state to "reserved"
    result = coupons_collection.find_one_and_update(
        {"_id": random_coupon["_id"]},
        {"$set": {"state": "reserved"}},
        return_document=ReturnDocument.AFTER
    )

    print(result)

    if result:
        return result['code']
    else:
        return 500


def create_project(title, description, image_url, project_id):
    db = create_connect_mongodb()
    projects_collection = db.projects

    project = {
        "project_id": project_id,
        "title": title,
        "description": description,
        "image_url": image_url
    }
    projects_collection.insert_one(project)

def get_project(project_id):
    db = create_connect_mongodb()
    projects_collection = db.projects

    return projects_collection.find_one({"project_id": project_id}, {"_id": 0})  # Excluding the MongoDB ObjectId


if __name__ == '__main__':
    app.run()
