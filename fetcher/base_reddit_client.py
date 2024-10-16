import hashlib
import logging
from datetime import datetime, timezone

import praw
from pymongo import MongoClient, errors

from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT, MONGO_URI


class BaseRedditClient:
    def __init__(self, subreddit_name, use_cache=True):
        self.reddit_instance = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT
        )
        self.mongo_client = MongoClient(MONGO_URI)
        self.cache_db = self.mongo_client["cache"]
        self.posts_cache_collection = self.cache_db["tmp"]
        self.use_cache = use_cache
        self.subreddit_name = subreddit_name


        self._ensure_ttl_index()
        logging.info('Base Reddit client initialized.')

    def __del__(self):
        try:
            if hasattr(self, 'mongo_client') and self.mongo_client:
                self.mongo_client.close()
                logging.info('MongoDB connection closed.')
        except Exception:
            pass  # Ignore any exceptions during shutdown

    def _ensure_ttl_index(self):
        """
        Creates a TTL index on the 'created_at' field to expire documents after 30 days.
        """
        try:
            self.posts_cache_collection.create_index(
                "created_at", expireAfterSeconds=2592000
            )
            logging.info("TTL index on 'created_at' ensured.")
        except errors.OperationFailure as e:
            logging.warning(f"TTL index creation skipped: {e}")

    def generate_cache_key(self):
        """
        Generates a SHA-256 hash based on the current date and subreddit.
        """
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cache_key_input = f"{today_str}_{self.subreddit_name}"
        cache_key = hashlib.sha256(cache_key_input.encode('utf-8')).hexdigest()
        logging.info(f"Generated cache key: {cache_key} for date: {today_str} and subreddit: r/{self.subreddit_name}")
        return cache_key, today_str

    def get_cached_posts(self, cache_key):
        """
        Retrieves cached posts from MongoDB based on the cache key.
        """
        if self.use_cache:
            cached_data = self.posts_cache_collection.find_one({"cache_key": cache_key})
            if cached_data:
                logging.info(f"Using cached posts for r/{self.subreddit_name} on {cached_data['date']}")
                return cached_data['posts']
        return None

    def cache_posts(self, cache_key, subreddit_name, today_str, posts):
        """
        Caches the fetched posts into MongoDB.
        """
        try:
            self.posts_cache_collection.insert_one({
                "cache_key": cache_key,
                "subreddit": subreddit_name,
                "date": today_str,
                "posts": posts,
                "created_at": datetime.now(timezone.utc)
            })
            logging.info(f"Stored cached posts for r/{self.subreddit_name} on {today_str}.")
        except errors.PyMongoError as e:
            logging.error(f"Error caching posts: {str(e)}")

    def fetch_posts(self, time_filter='year', limit=1000, search_term=None):
        """
        Fetches posts from the subreddit, utilizing caching and applying optional filters.
        If a search_term is provided, searches for posts containing the term within the specified time_filter.
        Otherwise, fetches the top posts.

        Parameters:
            time_filter (str): A string representing the time filter (e.g., 'day', 'week', 'month', 'year', 'all').
            limit (int): The maximum number of posts to retrieve.
            search_term (str, optional): The term to search for within the subreddit.

        Returns:
            list: A list of post data dictionaries.
        """
        try:
            cache_key, today_str = self.generate_cache_key()
            cached_posts = self.get_cached_posts(cache_key)
            if cached_posts:
                return cached_posts

            subreddit = self.reddit_instance.subreddit(self.subreddit_name)

            if search_term:
                fetched_posts = subreddit.search(query=search_term, time_filter=time_filter, limit=limit)
            else:
                fetched_posts = subreddit.top(time_filter=time_filter, limit=limit)

            posts = []

            for post in fetched_posts:
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'score': post.score,
                    'url': post.url,
                    'reddit_url': f"https://www.reddit.com{post.permalink}",
                    'num_comments': post.num_comments,
                    'created_utc': post.created_utc,
                    'subreddit': self.subreddit_name,
                    'comments': self.fetch_comments(post)
                }
                posts.append(post_data)

            self.cache_posts(cache_key, self.subreddit_name, today_str, posts)
            return posts
        except Exception as e:
            logging.exception("An error occurred while fetching posts.")
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

if __name__ == "__main__":
    reddit_client = BaseRedditClient(subreddit_name="podcasting", use_cache=False)
    posts = reddit_client.fetch_posts(time_filter='year', limit=None, search_term="mic or microphone")
    for post in posts:
        logging.info(f"Post: {post['title']} - Comments: {len(post['comments'])}")
        for comment in post['comments']:
            logging.info(f"  {comment['author']}: {comment['body']}")
