from pymongo import MongoClient
import os

def connect_to_mongo(host='localhost', port=27017, username=None, password=None, db_name='mydatabase'):
    """ Connect to MongoDB instance """
    if username and password:
        uri = f"mongodb://{username}:{password}@{host}:{port}/"
    else:
        uri = f"mongodb://{host}:{port}/"
    
    uri = os.environ["MONGO_DB_URI"]
    client = MongoClient(uri)
    db_name = os.environ["MONGO_DB_NAME"]
    return client[db_name]

def fetch_collection(db, collection_name):
    """ Fetch a collection from the database """
    return db[collection_name]

def fetch_all_records(collection):
    """ Fetch all records from a collection """
    return list(collection.find({}))

