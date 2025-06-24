from pymongo import MongoClient

def get_mongo_client():
    uri = "mongodb+srv://princek02032004:Snehal%401234@valuefy-cluster.spuzijz.mongodb.net/"
    client = MongoClient(uri)
    return client


def get_client_collection():
    client = get_mongo_client()
    db = client["valuefy"]  # This should match the name you gave in Atlas
    return db["clients"]    # Use the collection name you created in Atlas
