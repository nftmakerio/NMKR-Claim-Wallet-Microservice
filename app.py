from flask import Flask, request, jsonify
from pymongo import MongoClient
from config import username, password, BEARER_TOKEN
from coupon_generator import generate_multiple_coupon_codes, generate_coupon_code
from nmkr_api import mint_and_send_random
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app = Flask(__name__)
uri = "mongodb+srv://" + username + ":" + password + "@nmkrwalletclaster.ztafseg.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client.coupon_db
coupons_collection = db.coupons


@app.route('/create_coupons', methods=['POST'])
def create_coupons():
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


projects_collection = db.projects

def create_project(title, description, image_url, project_id):
    project = {
        "project_id": project_id,
        "title": title,
        "description": description,
        "image_url": image_url
    }
    projects_collection.insert_one(project)

def get_project(project_id):
    return projects_collection.find_one({"project_id": project_id}, {"_id": 0})  # Excluding the MongoDB ObjectId



if __name__ == '__main__':
    app.run(debug=True)