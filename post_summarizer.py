# Start Generation Here
import json
import logging
from pymongo import MongoClient, errors

from json_exporter import JSONExporter
from openai_chat_client import OpenAIChatClient
from config import MONGO_URI


SYSTEM_PROMPT = """

**Prompt:**

*You are an AI language model tasked with generating a concise 3-4 sentence description of a Reddit post based on its title and summarized comments. The description should capture the main topic, key points, and any significant debates or perspectives presented in the discussion. Keep it factual and clear, avoiding any reflections or opinions. Focus on summarizing the essence of the post and the core themes discussed in the comments.*

**Instructions:**

- **Input Format:**
  - The input will contain:
    - `title`: The title of the Reddit post.
    - `comment_summaries`: A series of summarized comments discussing different aspects of the post.

- **Output Requirements:**
  - Write a 3-4 sentence summary that:
    - Clearly describes what the post and discussion are about.
    - Highlights the key points from the summarized comments.
    - Focuses on the main issues or debates raised by the commenters.
    - Does not include any subjective reflections or opinions.

---

**Example Input:**

```json
{
    "title": "OpenAI plans to slowly raise prices to $44 per month ($528 per year)",
    "comment_summaries": [
        {
            "id": "post_2_c1",
            "score": 267,
            "comment_summary": "The top-level comment expresses a strong preference for using locally-run models over proprietary services like ChatGPT, emphasizing control, cost-effectiveness, and stability."
        },
        {
            "id": "post_2_c2",
            "score": 488,
            "comment_summary": "This comment discusses the implications of running AI models locally versus using cloud-based services, with a focus on OpenAI's competition, financial model, and sustainability."
        },
        {
            "id": "post_2_c3",
            "score": 191,
            "comment_summary": "Several comments reflect users' intention to stop using OpenAI services due to the price increase, with some users considering alternative AI solutions."
        },
        {
            "id": "post_2_c4",
            "score": 17,
            "comment_summary": "This comment highlights the negative reaction to OpenAI's shift away from open-source models and their call for AI regulation, alongside skepticism about users adopting local AI solutions."
        }
    ]
}
```

**Example Output:**

The community discusses OpenAI’s plan to raise subscription prices to $44 per month. Users express a strong preference for locally-run AI models, citing concerns about price increases and the desire for more control over proprietary services like ChatGPT. Commentary also explores OpenAI's competition, financial model, and the sustainability of its business practices. Additionally, there is debate over whether users will continue using OpenAI services or seek alternative AI solutions in response to the price hike.
"""

class PostSummarizer:
    def __init__(self, subreddit):
        self.subreddit = subreddit
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client["reddit"]
        self.processed_collection = self.db["processed"]
        self.openai_client = OpenAIChatClient(system_prompt=SYSTEM_PROMPT)

    def generate_descriptions(self):
        # Fetch the document for the subreddit
        document = self.processed_collection.find_one({"subreddit": self.subreddit})
        if not document:
            logging.error(f"No cached data found for subreddit '{self.subreddit}'. Aborting.")
            return

        logging.info(f"Generating descriptions for subreddit '{self.subreddit}'...")
        posts = document.get('posts', [])

        for post in posts:
            title = post.get('title', '')
            comment_summaries = [comment.get('comment_summary', '') for comment in post.get('comments', [])]

            input_data = {
                "title": title,
                "comment_summaries": comment_summaries
            }

            try:
                input_json = json.dumps(input_data)
                description = self.openai_client.get_response(input_json)
                post['description'] = description
            except Exception as e:
                logging.error(f"Error generating description for post '{post.get('id', 'N/A')}': {str(e)}")
                post['description'] = ""

        # Update the document in MongoDB
        try:
            self.processed_collection.update_one(
                {"subreddit": self.subreddit},
                {"$set": {"posts": posts}}
            )
            logging.info(f"Descriptions generated and updated for subreddit '{self.subreddit}'.")
        except errors.PyMongoError as e:
            logging.error(f"Error updating descriptions in MongoDB for subreddit '{self.subreddit}': {str(e)}")


if __name__ == "__main__":
    generator = PostSummarizer("LocalLLaMA")
    generator.generate_descriptions()

    # exporter = JSONExporter("LocalLLaMA")
    # exporter.export_to_json()
