import logging


from datetime import datetime, timedelta

from fetcher.base_reddit_client import BaseRedditClient


class RedditClient(BaseRedditClient):
    def __init__(
        self,
        subreddit_name,
        use_cache=True,
        filter_old_posts=False,
        num_posts=1000,
        time_filter='week'
    ):
        """
        Initializes the RedditClient with configurable options.

        Args:
            subreddit_name (str): Name of the subreddit to fetch posts from.
            use_cache (bool, optional): Whether to use caching. Defaults to True.
            filter_old_posts (bool, optional): Whether to filter out posts older than the specified time_filter. Defaults to True.
            num_posts (int, optional): Number of top posts to return after filtering. Defaults to 10.
            time_filter (str, optional): Time filter for fetching posts. Defaults to 'week'.
        """
        super().__init__(subreddit_name, use_cache)
        self.filter_old_posts = filter_old_posts
        self.num_posts = num_posts
        self.time_filter = time_filter

    def fetch_top_posts(self):
        """
        Fetches and filters top posts from the subreddit.
        """
        try:
            fetched_posts = self.fetch_posts(time_filter=self.time_filter, limit=self.num_posts * 20 if self.filter_old_posts else self.num_posts)
            if self.filter_old_posts:
                one_week_ago = datetime.utcnow() - timedelta(weeks=1)
                filtered_posts = [
                    post for post in fetched_posts
                    if datetime.utcfromtimestamp(post['created_utc']) >= one_week_ago
                ]
            else:
                filtered_posts = fetched_posts

            if self.num_posts:
                return filtered_posts[:self.num_posts]

            return filtered_posts
        except Exception as e:
            logging.exception("An error occurred while fetching top posts.")
            raise



def main():
    logging.basicConfig(level=logging.INFO)
    reddit_client = RedditClient(
        "podcasting",
        use_cache=True,           # Enable caching
        filter_old_posts=False,    # Enable filtering of posts older than the time_filter
        num_posts=1000,           # Number of posts to return after filtering
        time_filter='year'        # Time filter for fetching posts
    )
    top_posts = reddit_client.fetch_top_posts()
    logging.info(f"Fetched {len(top_posts)} posts.")

if __name__ == "__main__":
    main()
