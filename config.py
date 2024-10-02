import os

# Reddit API Credentials
CLIENT_ID = os.getenv('REDDIT_CLIENT_ID', 'your_client_id')
CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET', 'your_client_secret')
USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'your_user_agent')

# MongoDB Connection Details
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'reddit_data')

# Fetch Parameters
SUBREDDITS = ['python', 'learnprogramming', 'datascience']
NUM_POSTS = 10
TIME_FILTER = 'week'  # Options: 'all', 'day', 'hour', 'month', 'week', 'year'