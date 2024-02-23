from pymongo import MongoClient
from config import username, password

def create_connect_mongodb():
    uri = "mongodb+srv://" + username + ":" + password + "@nmkrwalletclaster.ztafseg.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri)

    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    return client.coupon_db
