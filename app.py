from flask import Flask, request, jsonify
from pymongo import MongoClient
from config import username, password
from coupon_generator import generate_multiple_coupon_codes, generate_coupon_code
from nmkr_api import mint_and_send_random
from flask_cors import CORS, cross_origin
from datetime import timedelta
from multiprocessing import Pool # for the multithreading

app = Flask(__name__)
CORS(app)

def create_connect_mongodb():
    uri = "mongodb+srv://" + username + ":" + password + "@nmkrwalletclaster.ztafseg.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)

    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    return client.coupon_db


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
    db = create_connect_mongodb()
    coupons_collection = db.coupons

    num_coupons = request.json.get('num_coupons')
    project_id = request.json.get('project_id')

    if not num_coupons or not project_id:
        return jsonify({"message": "Number of coupons and project ID required"}), 400

    # Generate the coupon codes
    coupon_codes = [generate_coupon_code() for _ in range(num_coupons)]

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


import requests
@app.route('/tarochi_endpoint', methods=['GET'])
def get_tarochi():
    BLOCKFROST_PROJECT_ID = "mainnetT0VVAzVt1QgWVVLxITkT8a4Dzn1QF6LN"
    ADDRESS = "addr1v9glhp7wdxnfk24jq4gjjsry6st8pjk5d6q39ctn83qx8gs9aq4te"
    SPECIFIC_ADDRESS = "addr1v9glhp7wdxnfk24jq4gjjsry6st8pjk5d6q39ctn83qx8gs9aq4te"

    TRANSACTIONS_ENDPOINT = f"https://cardano-mainnet.blockfrost.io/api/v0/addresses/{ADDRESS}/transactions"
    UTXOS_ENDPOINT = "https://cardano-mainnet.blockfrost.io/api/v0/txs/{}/utxos"

    headers = {"project_id": BLOCKFROST_PROJECT_ID}

    response = requests.get(TRANSACTIONS_ENDPOINT, headers=headers)
    transactions = response.json()

    transactions = sorted(transactions, key=lambda x: x["block_time"])

    transactions_list = []
    totalAmountPurchases = 0
    totalPurchasesOver40ADA = 0

    for transaction in transactions:
        totalAmountPurchases += 1
        tx_hash = transaction["tx_hash"]
        block_height = transaction["block_height"]
        block_time = transaction["block_time"]

        utxos_response = requests.get(UTXOS_ENDPOINT.format(tx_hash), headers=headers)
        utxos_data = utxos_response.json()

        lovelace_received = sum(int(utxo["amount"][0]["quantity"]) for utxo in utxos_data["outputs"] if utxo["address"] == SPECIFIC_ADDRESS)
        ada_amount = lovelace_received / 1_000_000

        if ada_amount > 40:
            totalPurchasesOver40ADA += 1

        output_to_specific_address = any(output["address"] == SPECIFIC_ADDRESS for output in utxos_data["outputs"])
        relevant_sender_addresses = set(utxo["address"] for utxo in utxos_data["inputs"] if output_to_specific_address)
        sender_address_str = ', '.join(relevant_sender_addresses)

        transactions_list.append({
            "tx_hash": tx_hash,
            "block_height": block_height,
            "block_time": block_time,
            "sender_address": sender_address_str,
            "ada_amount": ada_amount,
            "output_to_specific_address": output_to_specific_address
        })

    totalTransactions = len(transactions_list)
    totalPurchasesBelow40ADA = totalTransactions - totalPurchasesOver40ADA

    response_data = {
        "transactions": transactions_list,
        "totalAmountPurchases": totalAmountPurchases,
        "totalPurchasesOver40ADA": totalPurchasesOver40ADA,
        "totalTransactions": totalTransactions,
        "totalPurchasesBelow40ADA": totalPurchasesBelow40ADA
    }

    return jsonify(response_data), 200

if __name__ == '__main__':
    app.run()
