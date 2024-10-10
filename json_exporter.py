import json
import logging
from abc import ABC, abstractmethod

from pymongo import MongoClient

from config import MONGO_URI


class BaseExporter(ABC):
    def __init__(self, subreddit):
        self.subreddit = subreddit
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client["reddit"]
        self.cache_collection = self.db[subreddit]

    def get_posts(self):
        document = self.cache_collection.find_one({"subreddit": self.subreddit})
        if not document:
            logging.error(f"No cached data found for subreddit '{self.subreddit}'. Aborting.")
            return []
        return document.get('posts', [])

    @abstractmethod
    def export(self, output_file):
        pass


class JSONExporter(BaseExporter):
    def export(self, output_file='output.json'):
        posts = self.get_posts()

        # Prepare data with only the required fields
        filtered_posts = []
        for post in posts:
            filtered_comments = self.process_comments(post.get('comments', []))
            filtered_post = {
                'id': post.get('id', ''),
                'title': post.get('title', 'No Title'),
                'description': post.get('description', 'No Description'),
                'upvotes': post.get('upvotes', 0),
                'rank': post.get('rank', 0),
                'comments': filtered_comments
            }
            filtered_posts.append(filtered_post)

        # Write the filtered data to a JSON file
        try:
            with open(output_file, 'w', encoding='utf-8') as json_file:
                json.dump(filtered_posts, json_file, ensure_ascii=False, indent=4)
            logging.info(f"JSON export completed. File saved as '{output_file}'.")
        except Exception as e:
            logging.error(f"Failed to write JSON file '{output_file}': {str(e)}")

    def process_comments(self, comments):
        """
        Recursively process comments to keep only 'id', 'score', and 'comment_summary'.
        """
        filtered = []
        for comment in comments:
            filtered_comment = {
                'id': comment.get('id', ''),
                'score': comment.get('score', 0),
                'comment_summary': comment.get('comment_summary', '')
            }
            filtered.append(filtered_comment)
        return filtered


class MarkdownExporter(BaseExporter):
    def export(self, output_file='output.md'):
        posts = self.get_posts()

        try:
            with open(output_file, 'w', encoding='utf-8') as md_file:
                md_file.write(f"# Top Posts from r/{self.subreddit} This Week\n\n")
                for post in posts:
                    rank = post.get('rank', 0)
                    title = post.get('title', 'No Title')
                    url = post.get('url', '')
                    upvotes = post.get('upvotes', 0)
                    description = post.get('description', 'No Description')

                    md_file.write(f"## {rank}. {title}\n\n")
                    md_file.write(f"**URL:** {url}\n\n")
                    md_file.write(f"**Upvotes:** {upvotes}\n\n")
                    md_file.write(f"**Description:** {description}\n\n")
                    md_file.write("---\n\n")

            logging.info(f"Markdown export completed. File saved as '{output_file}'.")
        except Exception as e:
            logging.error(f"Failed to write Markdown file '{output_file}': {str(e)}")


if __name__ == "__main__":
    markdown_exporter = MarkdownExporter("LocalLLaMA")
    markdown_exporter.export()
