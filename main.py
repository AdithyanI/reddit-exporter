from reddit_client import fetch_top_posts
from mongo_client import store_posts

def main():
    print("Starting Reddit Data Aggregator...")
    posts = fetch_top_posts()
    print(f"Fetched {len(posts)} posts.")
    store_posts(posts)
    print("Data has been successfully stored in MongoDB.")

if __name__ == "__main__":
    main()