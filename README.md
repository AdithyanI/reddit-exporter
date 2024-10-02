# Reddit Data Aggregator

A simple Python script to fetch top posts and comments from specified subreddits using the Reddit API and store them in MongoDB for easy access and analysis.

## Project Description

This project aims to:

- Fetch the top **X** posts from selected subreddits over a configurable time period (e.g., the last week).
- Retrieve detailed information about each post, including its comments.
- Store the fetched data in MongoDB in an organized structure.
- Provide an easy-to-understand and maintainable codebase suitable for hobby projects.

## Features

- **Configurable Parameters**: Easily adjust the number of posts to fetch, time frame, and target subreddits.
- **Data Storage**: Efficiently stores posts and comments in MongoDB for later use.
- **Simplicity**: Written with simplicity and readability in mind, making it easy to modify and extend.

## Project Structure

```
reddit_data_aggregator/
├── reddit_data_aggregator.py
├── config.py
├── reddit_client.py
├── mongo_client.py
├── requirements.txt
└── README.md
```

- **`reddit_data_aggregator.py`**: The main script that orchestrates the data fetching and storing process.
- **`config.py`**: Contains all configurable settings such as API credentials and fetch parameters.
- **`reddit_client.py`**: Handles interactions with the Reddit API.
- **`mongo_client.py`**: Manages MongoDB connections and database operations.
- **`requirements.txt`**: Lists the Python dependencies required for the project.
- **`README.md`**: Provides an overview and instructions for the project.

## Configuration

All configuration settings are stored in the `config.py` file:

- **Reddit API Credentials**:
  - `CLIENT_ID`
  - `CLIENT_SECRET`
  - `USER_AGENT`

- **MongoDB Connection Details**:
  - `MONGO_URI`
  - `DATABASE_NAME`

- **Fetch Parameters**:
  - `SUBREDDITS`: List of subreddits to fetch posts from.
  - `NUM_POSTS`: Number of top posts to retrieve from each subreddit.
  - `TIME_FILTER`: Time frame for top posts (e.g., `'day'`, `'week'`, `'month'`).

## Requirements

- **Python 3.x**
- **MongoDB**
- **Python Packages**:
  - `praw` (Python Reddit API Wrapper)
  - `pymongo`

## Installation and Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your_username/reddit_data_aggregator.git
   cd reddit_data_aggregator
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Reddit API Credentials**

   - Create a Reddit account if you don't have one.
   - Go to [Reddit Apps](https://www.reddit.com/prefs/apps) and create a new script application.
   - Obtain your `CLIENT_ID`, `CLIENT_SECRET`, and set a `USER_AGENT`.

5. **Configure the Application**

   - Open `config.py` and fill in your Reddit API credentials.
   - Update MongoDB connection details if necessary.
   - Adjust fetch parameters (`SUBREDDITS`, `NUM_POSTS`, `TIME_FILTER`) as desired.

## Usage

1. **Run the Script**

   ```bash
   python reddit_data_aggregator.py
   ```

2. **Verify Data Storage**

   - Use MongoDB Compass or the MongoDB shell to check that data has been stored correctly in your database.

## Customization

- **Adding Subreddits**: Modify the `SUBREDDITS` list in `config.py` to include any subreddits you're interested in.
- **Changing Time Frame**: Adjust the `TIME_FILTER` in `config.py` to change the period for top posts.
- **Number of Posts**: Set `NUM_POSTS` in `config.py` to control how many posts are fetched from each subreddit.

## Optional Enhancements

- **Automation**: Set up a cron job or scheduled task to run `main.py` at regular intervals.
- **Data Analysis**: Create additional scripts to analyze the stored data.
- **Logging**: Implement logging to keep track of the script's operations and errors.

## Troubleshooting

- **Authentication Errors**: Ensure that your Reddit API credentials in `config.py` are correct.
- **Database Connection Issues**: Verify that MongoDB is running and that the `MONGO_URI` in `config.py` is accurate.
- **Dependencies**: Make sure all required Python packages are installed by running `pip install -r requirements.txt`.

## License

This project is for personal use and experimentation. Feel free to modify and extend it as you like.

## Acknowledgements

- **PRAW**: [https://praw.readthedocs.io/](https://praw.readthedocs.io/)
- **PyMongo**: [https://pymongo.readthedocs.io/](https://pymongo.readthedocs.io/)

