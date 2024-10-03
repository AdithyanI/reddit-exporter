import logging
import praw
from config import CLIENT_ID, CLIENT_SECRET, USER_AGENT, SUBREDDITS, NUM_POSTS, TIME_FILTER

class RedditClient:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT
        )
        logging.info('Reddit client initialized')
    
    def fetch_top_posts(self):
        try:
            all_posts = []
            for subreddit in SUBREDDITS:
                logging.info(f"Fetching top posts from r/{subreddit}")
                subreddit_instance = self.reddit.subreddit(subreddit)
                top_posts = subreddit_instance.top(time_filter=TIME_FILTER, limit=NUM_POSTS)
                for post in top_posts:
                    post_data = {
                        'id': post.id,
                        'title': post.title,
                        'score': post.score,
                        'url': post.url,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc,
                        'comments': self.fetch_comments(post)
                    }
                    all_posts.append(post_data)
            return all_posts
        except Exception as e:
            logging.exception("An error occurred while fetching top posts.")
            raise

    def fetch_comments(self, post):
        try:
            post.comments.replace_more(limit=0)
            comments = []
            for comment in post.comments.list():
                comments.append({
                    'id': comment.id,
                    'body': comment.body,
                    'score': comment.score,
                    'created_utc': comment.created_utc,
                    'author': str(comment.author)
                })
            return comments
        except Exception as e:
            logging.exception(f"An error occurred while fetching comments for post {post.id}.")
            raise

def main():
    logging.basicConfig(level=logging.INFO)
    client = RedditClient()
    posts = client.fetch_top_posts()
    logging.info(f"Fetched {len(posts)} posts.")

if __name__ == "__main__":
    main()

