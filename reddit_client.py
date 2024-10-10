import logging
import praw
from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    USER_AGENT,
    NUM_POSTS,
    TIME_FILTER,
    MONGO_URI
)
from pymongo import MongoClient, errors
from datetime import datetime

class RedditClient:
    def __init__(self, subreddit, use_cache=True):
        self.reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT
        )
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client["cache"]
        self.cache_collection = self.db["tmp"]
        self._ensure_ttl_index()
        self.subreddit = subreddit
        self.use_cache = use_cache
        logging.info('Reddit client initialized')

    def __del__(self):
        if hasattr(self, 'mongo_client') and self.mongo_client:
            self.mongo_client.close()
            logging.info('MongoDB connection closed')

    def _ensure_ttl_index(self):
        """
        Creates a TTL index on the 'created_at' field to expire documents after 30 days.
        """
        try:
            self.cache_collection.create_index(
                "created_at", expireAfterSeconds=2592000
            )
            logging.info("TTL index on 'created_at' ensured.")
        except errors.OperationFailure as e:
            logging.warning(f"TTL index creation skipped: {e}")

    def fetch_top_posts(self):
        """
        Fetches top posts from specified subreddit, utilizing caching to minimize API calls.
        """
        try:
            logging.info(f"Fetching top posts from r/{self.subreddit}")

            # Check cache before making API call
            if self.use_cache:
                cached_posts = self.cache_collection.find_one({"subreddit": self.subreddit})
                if cached_posts:    
                    logging.info(f"Using cached posts for r/{self.subreddit}")
                    return cached_posts['posts']

            subreddit_instance = self.reddit.subreddit(self.subreddit)
            top_posts = subreddit_instance.top(
                time_filter=TIME_FILTER, limit=NUM_POSTS
            )
            subreddit_posts = []
            # Start of Selection
            for post in top_posts:
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'score': post.score,
                    'url': post.url,
                    'reddit_url': f"https://www.reddit.com{post.permalink}",
                    'num_comments': post.num_comments,
                    'created_utc': post.created_utc,
                    'subreddit': self.subreddit,
                    'comments': self.fetch_comments(post)
                }
                subreddit_posts.append(post_data)

            # Store fetched posts in cache
            self.cache_collection.insert_one({
                "subreddit": self.subreddit,
                "posts": subreddit_posts,
                "created_at": datetime.utcnow()
            })

            return subreddit_posts
        except Exception as e:
            logging.exception("An error occurred while fetching top posts.")
            raise

    def fetch_comments(self, post):
        """
        Fetches all comments for a given post.
        """
        try:
            post.comments.replace_more(limit=None)  # Fetch all comments
            return self.process_comments(post.comments)
        except Exception as e:
            logging.exception(f"An error occurred while fetching comments for post {post.id}.")
            raise

    def process_comments(self, comments):
        """
        Processes a list of comments recursively.
        """
        processed_comments = []
        for comment in comments:
            comment_data = self.process_comment(comment)
            processed_comments.append(comment_data)
        return processed_comments

    def process_comment(self, comment):
        """
        Recursively processes a single comment and its replies.
        """
        comment_dict = {
            'id': comment.id,
            'author': str(comment.author),
            'body': comment.body,
            'score': comment.score,
            'created_utc': comment.created_utc,
            'replies': self.process_comments(comment.replies)  # Recursively process replies
        }
        return comment_dict

def main():
    logging.basicConfig(level=logging.INFO)
    client = RedditClient("LocalLLaMA", use_cache=False)  # Example subreddit
    posts = client.fetch_top_posts()
    logging.info(f"Fetched {len(posts)} posts.")

if __name__ == "__main__":
    main()
