import logging
from pymongo import MongoClient
from config import MONGO_URI, DATABASE_NAME

class MongoClientWrapper:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DATABASE_NAME]
        self.posts_collection = self.db['posts']
    
    def store_posts(self, posts):
        try:
            result = self.posts_collection.insert_many(posts)
            logging.info(f"Inserted {len(result.inserted_ids)} posts into the database.")
        except Exception as e:
            logging.exception("An error occurred while storing posts to MongoDB.")
            raise

def main():
    logging.basicConfig(level=logging.INFO)
    mongo_client = MongoClientWrapper()
    sample_posts = [
        {
            'id': 'test1',
            'title': 'Test Post 1',
            'score': 100,
            'url': 'http://example.com/test1',
            'num_comments': 10,
            'created_utc': 1609459200,
            'comments': []
        },
        {
            'id': 'test2',
            'title': 'Test Post 2',
            'score': 200,
            'url': 'http://example.com/test2',
            'num_comments': 20,
            'created_utc': 1609459300,
            'comments': []
        }
    ]
    mongo_client.store_posts(sample_posts)

if __name__ == "__main__":
    main()