import logging
from reddit_client import fetch_top_posts
from mongo_client import store_posts

class RedditDataAggregator:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("app.log"),
                logging.StreamHandler()
            ]
        )
    
    def run(self):
        try:
            logging.info("Starting Reddit Data Aggregator...")
            posts = fetch_top_posts()
            logging.info(f"Fetched {len(posts)} posts.")
            if posts:
                store_posts(posts)
                logging.info("Data has been successfully stored in MongoDB.")
            else:
                logging.info("No posts fetched, skipping storing to MongoDB.")
        except Exception as e:
            logging.exception("An error occurred in the main process.")

if __name__ == "__main__":
    aggregator = RedditDataAggregator()
    aggregator.run()