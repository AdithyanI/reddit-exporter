from dotenv import load_dotenv
import os

# Load variables from .env file
load_dotenv()

# Reddit API Credentials
CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
USER_AGENT = os.getenv('REDDIT_USER_AGENT')

# MongoDB Connection Details
MONGO_URI = os.getenv('MONGO_URI')
DATABASE_NAME = os.getenv('DATABASE_NAME')

# Fetch Parameters
SUBREDDITS = ['LocalLLaMA']
NUM_POSTS = 10
TIME_FILTER = 'week'  # Options: 'all', 'day', 'hour', 'month', 'week', 'year'