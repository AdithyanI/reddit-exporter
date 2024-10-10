import logging

import hashlib

from openai_chat_client import OpenAIChatClient
from reddit_client import RedditClient
from datetime import datetime, timezone
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pymongo import MongoClient, errors
from config import MONGO_URI  # Ensure MONGO_URI is imported from your config

class RedditPostProcessor:
    def __init__(self, subreddit):
        self.reddit_client = RedditClient(subreddit)
        self.subreddit = subreddit
        logging.info('RedditPostProcessor initialized.')

    def filter_posts(self, posts):
        sorted_posts = sorted(posts, key=lambda x: x['score'], reverse=True)
        
        processed_posts = []
        for rank, post in enumerate(sorted_posts, start=1):
            post_id = f"post_{rank}"
            processed_post = {
                'id': post_id,
                'url': post['url'],
                'reddit_url': post['reddit_url'],
                'title': post['title'],
                'upvotes': post['score'],
                'rank': rank,
                'comments': self.filter_comments(post['comments'], parent_id=post_id, comment_type='c', is_top_level=True)
            }
            processed_posts.append(processed_post)
        return processed_posts

    def filter_comments(self, comments, parent_id, comment_type='c', is_top_level=False):
        filtered = []
        for idx, comment in enumerate(comments, start=1):
            score_threshold = 10 if is_top_level else 3
            if comment['score'] >= score_threshold:
                comment_id = f"{parent_id}_{comment_type}{idx}"
                filtered_comment = {
                    'id': comment_id,
                    'text': comment['body'],
                    'score': comment['score']
                }
                next_comment_type = 'r'
                replies = self.filter_comments(comment.get('replies', []), parent_id=comment_id, comment_type=next_comment_type, is_top_level=False)
                if replies:
                    filtered_comment['replies'] = replies
                filtered.append(filtered_comment)
        return filtered

    def summarize_comment_with_openai(self, comment):
        client = OpenAIChatClient()
        response = client.get_response(json.dumps(comment))
        return response

    def summarize_comments(self, filtered_posts):
        with ThreadPoolExecutor(max_workers=10) as executor:
            for post in filtered_posts:
                futures = {executor.submit(self.summarize_comment_with_openai, comment): comment for comment in post.get('comments', [])}
                for future in futures:
                    comment = futures[future]
                    try:
                        summary = future.result()
                        comment['comment_summary'] = summary
                    except Exception as e:
                        logging.error(f"Error summarizing comment {comment['id']}: {str(e)}")
        return filtered_posts

    def process_subreddit(self):
        with MongoClient(MONGO_URI) as mongo_client:
            db = mongo_client["reddit"]
            cache_collection = db["processed"]

            # Generate cache key based on today's date and subreddit
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            cache_key_input = f"{today_str}_{self.subreddit}"
            cache_key = hashlib.sha256(cache_key_input.encode('utf-8')).hexdigest()

            # Check if processed posts already exist in MongoDB
            cached_data = cache_collection.find_one({"cache_key": cache_key})
            if cached_data:
                logging.info(f"Processed posts for subreddit '{self.subreddit}' on {today_str} already exist in MongoDB. Skipping processing.")
                return
            
            posts = self.reddit_client.fetch_top_posts()
            
            filtered_posts = self.filter_posts(posts)
            comment_summarized_posts = self.summarize_comments(filtered_posts)
            
            # Store the processed posts in MongoDB
            try:
                cache_collection.insert_one({
                    "cache_key": cache_key,
                    "subreddit": self.subreddit,
                    "posts": comment_summarized_posts,
                    "date": today_str,
                    "created_at": datetime.utcnow()
                })
                logging.info(f"Stored processed posts for subreddit '{self.subreddit}' on {today_str} in MongoDB.")
            except errors.PyMongoError as e:
                logging.error(f"Error storing processed posts to MongoDB for subreddit {self.subreddit}: {str(e)}")

def main():
    logging.basicConfig(level=logging.INFO)
    processor = RedditPostProcessor("LocalLLaMA")  # Example subreddit
    processor.process_subreddit()

if __name__ == "__main__":
    main()
