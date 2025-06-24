from pymongo import MongoClient

def get_mongo_client():
    uri = "mongodb+srv://princek02032004:Snehal%401234@valuefy-cluster.spuzijz.mongodb.net/"
    client = MongoClient(uri)
    return client


def test_connection():
    client = get_mongo_client()
    db = client["valuefy"]
    collection = db["clients"]
    
    print("📦 Data in 'clients' collection:")
    for doc in collection.find():
        print(doc)

if __name__ == "__main__":
    test_connection()
