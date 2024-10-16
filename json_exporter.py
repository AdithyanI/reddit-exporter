import json
import logging
from abc import ABC, abstractmethod

from pymongo import MongoClient

from config import MONGO_URI

SYSTEM_INSTRUCTIONS = """<system_instructions>

The following is a set of instructions to guide your podcast creation process. These instructions are not to be used directly in creating the script, but rather to inform the structure and approach you take when crafting the podcast content. The actual content for the podcast will be based on the JSON data provided below these instructions. Please use these guidelines to shape your podcast creation, while drawing the specific content from the JSON data.


*You are an AI language model tasked with creating a podcast script for "Last Week In r/LocalLLaMA," a weekly roundup of the most interesting discussions, debates, and moments from the r/LocalLLaMA community. The goal is to provide listeners with a fun and lighthearted summary of the top posts, user opinions, and trending topics from the subreddit for the week ending on October 10th.*

*You have the following data for the top 10 posts, ranked from highest to lowest based on upvotes:*

- **Each post includes:**
- **Upvotes**: The number of upvotes the post received.
- **Rank**: The position of the post in the top 10 list.
- **Title**: The title of the post.
- **Description**: A brief description of the post content.
- **Comments**: A list of comments, each with:
- **ID**: The unique identifier of the comment.
- **Score**: The upvote score of the comment (indicating its popularity).
- **Comment Summary**: A summary of the discussion within that comment thread.

*When creating the podcast script, keep in mind:*

- **Structure:** Use the provided data to guide the content of the podcast. Each post's description and its top comment summaries should form the basis of your script.
- **Emphasis on Scores:** Give more weight to comments with higher scores when deciding which discussions to highlight. These comments are more authoritative and reflect the community's interests.
- **Content Preservation:** Preserve as much valuable information as possible from the descriptions and comment summaries. Include notable details and insights that would be interesting to listeners.

*Using this data, write an engaging and informative podcast script that:*

1. **Introduction:**
- Starts with a warm and welcoming introduction to the podcast and its purpose.
- Mentions the date or week being covered (e.g., "Welcome to 'Last Week In r/LocalLLaMA' for the week ending October 10th").

2. **Main Content:**
- For each of the top 10 posts:
- Introduce the post by its rank and title (e.g., "Coming in at number one, we have...").
- Provide a concise and engaging description of the post.
- Highlight the most significant discussions from the comments, prioritizing those with higher scores.
- Summarize the key points from the highest-scoring comments.
- Include notable quotes or verbatim text from top comments if they add value.
- Ensure that the discussions reflect the community's interests and opinions as represented by the scores.

3. **Conclusion:**
- Wrap up the podcast with closing remarks.
- Encourage listeners to join the subreddit if they haven't already.
- Provide a teaser or anticipation for the next week's episode.

*Additional Guidelines:*

- **Tone and Style:**
- Maintain a friendly, conversational tone suitable for a podcast audience.
- Keep the language clear and accessible.
- Inject lighthearted humor or enthusiasm where appropriate to keep listeners engaged.

- **Formatting:**
- Write the script in a format suitable for a text-to-voice model to read aloud.
- Use clear markers for different sections (e.g., "Introduction," "Post 1," "Transition," "Conclusion").

- **Content Selection:**
- When selecting which discussions to include, focus on comments with higher scores.
- Ensure that the summaries of discussions are comprehensive but concise, capturing the essence of the conversations.

*Example Structure:*

---

**Introduction:**

*"Hello and welcome to 'Last Week In r/LocalLLaMA,' your weekly roundup of the most exciting discussions and moments from the r/LocalLLaMA community. I'm your host, and today we'll be diving into the top posts for the week ending October 10th. Whether you missed out on the action or just want a refresher, we've got you covered!"*

**Post 1:**

*"Starting off at number one with 944 upvotes, we have 'OpenAI's new Whisper Turbo model running 100% locally in your browser with Transformers.js.'*

*The discussion revolves around OpenAI's new Whisper Turbo model, which can run entirely locally in web browsers using Transformers.js. Users reported impressive performance, with the ability to transcribe audio at about 10 times real-time speed. The community explored various aspects of the model, including its local execution, size of approximately 300MB, browser compatibility limited to Chromium browsers, and efficient memory management.*

*In the comments, several key points stood out:*

- *A highly upvoted comment clarified concerns about local execution, stating, "It's using transformers.js and WebGPU, so locally on the browser," confirming that the model runs entirely on the user's device without relying on external servers.*

- *Another significant discussion focused on the model's architecture. One user explained that the reduction in decoding layers from 32 to 4 results in faster processing with only minor quality degradation, aligning more closely with standard practices in the speech-to-text community.*

- *Users also shared practical tips, such as how the model files are stored in the browser's cache storage for faster subsequent loads and how to locate these cached files.*

- *The community expressed excitement about the ability to run sophisticated AI models locally and collaboratively worked through technical challenges, showcasing the innovative spirit of r/LocalLLaMA.*

**Transition:**

*"Moving on to number two..."*

**[Repeat the structure for Posts 2-10, ensuring you highlight the most significant discussions based on comment scores]**

**Conclusion:**

*"And that wraps up our highlights for this week! Thanks for tuning into 'Last Week In r/LocalLLaMA.' If you enjoyed these discussions, be sure to join us on the subreddit and jump into the conversation. We've got more exciting content coming up next week, so stay tuned. Until then, happy coding and exploring!"*

---

*Use this structure and guidelines to craft the complete podcast script based on your data. Remember to give appropriate weight to comments based on their scores when selecting which discussions to highlight.*

---
</system_instructions>
"""

class BaseExporter(ABC):
    def __init__(self, subreddit):
        self.subreddit = subreddit
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client["reddit"]
        self.cache_collection = self.db["processed"]

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
    # markdown_exporter = JSONExporter("LocalLLaMA")
    # markdown_exporter.export()

    markdown_exporter = MarkdownExporter("podcasting")
    markdown_exporter.export()
