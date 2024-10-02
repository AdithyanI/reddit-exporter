from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME

def get_mongo_client():
    client = MongoClient(MONGO_URI)
    return client

def get_database():
    client = get_mongo_client()
    db = client[DATABASE_NAME]
    return db

def store_posts(posts):
    db = get_database()
    posts_collection = db['posts']
    result = posts_collection.insert_many(posts)
    print(f"Inserted {len(result.inserted_ids)} posts into the database.")