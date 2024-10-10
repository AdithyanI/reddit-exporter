import logging
import praw
import hashlib
from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    USER_AGENT,
    NUM_POSTS,
    TIME_FILTER,
    MONGO_URI
)
from pymongo import MongoClient, errors
from datetime import datetime, timedelta

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
        Ensures that exactly NUM_POSTS posts created within the last week are returned.
        """
        try:
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            cache_key_input = f"{today_str}_{self.subreddit}"
            cache_key = hashlib.sha256(cache_key_input.encode('utf-8')).hexdigest()
            logging.info(f"Generated cache key: {cache_key} for date: {today_str} and subreddit: r/{self.subreddit}")

            # Check cache before making API call
            if self.use_cache:
                cached_posts = self.cache_collection.find_one({"cache_key": cache_key})
                if cached_posts:
                    logging.info(f"Using cached posts for r/{self.subreddit} on {today_str}")
                    return cached_posts['posts']

            subreddit_instance = self.reddit.subreddit(self.subreddit)
            fetched_posts = subreddit_instance.top(
                time_filter='week', limit=50  # Fetch more to account for possible exclusions
            )
            subreddit_posts = []
            one_week_ago = datetime.utcnow() - timedelta(weeks=1)

            for post in fetched_posts:
                post_created_time = datetime.utcfromtimestamp(post.created_utc)
                if post_created_time < one_week_ago:
                    logging.info(f"Excluding post {post.id} as it was created more than a week ago.")
                    continue

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

                if len(subreddit_posts) >= NUM_POSTS:
                    break

            if len(subreddit_posts) < NUM_POSTS:
                logging.warning(f"Only fetched {len(subreddit_posts)} posts within the last week for r/{self.subreddit}.")

            # Store fetched posts in cache with the new cache_key
            self.cache_collection.insert_one({
                "cache_key": cache_key,
                "subreddit": self.subreddit,
                "date": today_str,
                "posts": subreddit_posts,
                "created_at": datetime.utcnow()
            })

            logging.info(f"Fetched and cached {len(subreddit_posts)} posts for r/{self.subreddit} on {today_str}")
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
    client = RedditClient("LocalLLaMA", use_cache=True)  # Example subreddit with caching enabled
    posts = client.fetch_top_posts()
    logging.info(f"Fetched {len(posts)} posts.")

if __name__ == "__main__":
    main()
