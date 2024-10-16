import os
import logging
from openai import OpenAI


SYSTEM_PROMPT_COMMENT_SUMMARY = """
*You are an AI language model tasked with summarizing the comments of a single Reddit post. The goal is to create a comprehensive summary that preserves as much information as possible from the comments, with the eventual aim of summarizing the entire post for inclusion in a podcast. Focus on thoroughly understanding the discussion, capturing all significant points, insights, and nuances. High-score comments are more authoritative and should be given more weight in the summary. Include verbatim text from high-score comments where appropriate to preserve the original essence.*

**Instructions:**

- **Input Format:**

  - The input will be a JSON object representing the comments of a single Reddit post. Each comment object contains:

    - `id`: The unique identifier of the comment.

    - `text`: The content of the comment.

    - `score`: The score (upvotes) of the comment.

    - `replies`: A list of nested reply objects following the same structure.

- **Output Requirements:**

  - Provide a detailed and comprehensive summary that:

    - Preserves as much information as possible from the comments and their replies.

    - Emphasizes and gives more weight to high-score comments, including verbatim text where impactful.

    - Captures all key points, ideas, arguments, and nuances presented in the discussion.

    - Maintains logical flow and coherence, accurately reflecting the structure and progression of the conversation.

  - The summary should be in clear, coherent English, suitable for creating an in-depth summary of the post.

**Example Input:**

```json
{
  "id": "post_1_c1",
  "text": "Earlier today, OpenAI released a new Whisper model (Turbo), and now it can run locally in your browser with Transformers.js! I was able to achieve ~10x real-time factor (RTF), transcribing 120 seconds of audio in ~12 seconds on an M3 Max. Important links:\n\n- ONNX model: https://huggingface.co/onnx-community/whisper-large-v3-turbo\n- Source code: https://github.com/xenova/whisper-web/tree/experimental-webgpu\n- Demo: https://huggingface.co/spaces/webml-community/whisper-large-v3-turbo-webgpu",
  "score": 139,
  "replies": [
    {
      "id": "post_1_c1_r1",
      "text": "Is there a CPU version of this, like Whisper Web?",
      "score": 30
    },
    {
      "id": "post_1_c1_r3",
      "text": "Is it just acting as middleware and hitting OpenAI servers for actual inference?",
      "score": 9,
      "replies": [
        {
          "id": "post_1_c1_r3_r1",
          "text": "I read the code. It's using Transformers.js and WebGPU. So locally on the browser.",
          "score": 96,
          "replies": [
            {
              "id": "post_1_c1_r3_r1_r1",
              "text": "I don't get it. How does it load an 800MB file and run it on the browser itself? Where does the model get stored? I tried it and it is fast. Doesn't feel like there was a download too.",
              "score": 33,
              "replies": [
                {
                  "id": "post_1_c1_r3_r1_r1_r1",
                  "text": "It does take a while to download for the first time. The model files are then stored in the browser's cache storage.",
                  "score": 41
                },
                {
                  "id": "post_1_c1_r3_r1_r1_r2",
                  "text": "This is the model used. It's 300MB. With 100 MBit/s it's 30 seconds, with GBit it's only 3 seconds. For some weird reason, in-browser it downloads really slow for me...\n\nDownload only starts after you click 'Transcribe Audio'.\n\n*Edit*: Closing DevTools makes the download go fast.",
                  "score": 5
                }
              ]
            },
            {
              "id": "post_1_c1_r3_r1_r2",
              "text": "Thanks for doing the due diligence that some of us can't!",
              "score": 13
            }
          ]
        }
      ]
    }
  ]
}
```

**Example Output:**

"OpenAI has released a new Whisper model called Turbo, which can now run locally in your browser using Transformers.js and WebGPU. The original poster achieved approximately 10x real-time transcription speed, processing 120 seconds of audio in about 12 seconds on an M3 Max. They provided important links to the ONNX model, source code, and a demo for users to try out.

A user asked, 'Is there a CPU version of this, like Whisper Web?' indicating interest in broader hardware support beyond WebGPU.

Another commenter inquired, 'Is it just acting as middleware and hitting OpenAI servers for actual inference?' This concern was addressed by a highly upvoted reply (score: 96) stating, 'I read the code. It's using Transformers.js and WebGPU. So locally on the browser,' confirming that the model runs entirely client-side without server involvement.

The discussion delved deeper into technical aspects when a user questioned how the browser handles such a large model file: 'I don't get it. How does it load an 800MB file and run it on the browser itself? Where does the model get stored? I tried it and it is fast. Doesn't feel like there was a download too.' Another user (score: 41) explained, 'It does take a while to download for the first time. The model files are then stored in the browser's cache storage,' highlighting the use of caching for improved performance on subsequent uses.

Additional details were provided about the model size and download times. One commenter noted, 'This is the model used. It's 300MB. With 100 MBit/s it's 30 seconds, with GBit it's only 3 seconds. For some weird reason, in-browser it downloads really slow for me... Download only starts after you click "Transcribe Audio". *Edit*: Closing DevTools makes the download go fast,' pointing out potential issues with download speeds and how to mitigate them.

Appreciation was shown for the technical insights shared, with a user expressing, 'Thanks for doing the due diligence that some of us can't!' This emphasizes the community's value of shared knowledge and troubleshooting.

Overall, the comments reflect excitement about the new model's capabilities to run locally in the browser, questions about its technical implementation, and collaborative efforts to understand and optimize its performance."
"""


SYSTEM_PROMPT_COMMENT_MIC = """
You are given a Reddit post. Your task is to analyze the post only for microphone recommendations. Follow these steps:

Mic Recommendations Detection:
Check if there are any microphone recommendations mentioned in the post.
If yes, extract the names of the microphones and summarize what the user said about each one. This includes any details such as pros, cons, or specific use cases.
Output Format:
If microphone recommendations are found, provide the microphone name(s) and the summary for each.
If there are no microphone recommendations and the text is something else, return only the string "None".
Example Output Format:

Mic Recommendations:
[Microphone Name 1]: Summary of what the user said about this mic.
[Microphone Name 2]: Summary of what the user said about this mic.
No Recommendations:
None
"""






class OpenAIChatClient:
    def __init__(self, system_prompt: str=SYSTEM_PROMPT_COMMENT_MIC, model: str = "claude-3.5-sonnet-bedrock"):
        self.client = OpenAI(
            api_key="sk-5ce0c5c0-4079-11ef-9254-173e6ea885c7",
            base_url="http://217.86.140.15:4000"
        )
        self.system_prompt = system_prompt
        self.model = model
        logging.info("OpenAIChatClient initialized with system prompt.")

    def get_response(self, user_message: str) -> str:
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
            },
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.client.chat.completions.create(
                messages=messages,
                model=self.model
            )
            return response.choices[0].message.content

        except Exception as e:
            logging.exception("Failed to get response from OpenAI.")
            raise e
        
if __name__ == "__main__":
    client = OpenAIChatClient("You are an AI assistant tasked with analyzing legal documents.", model="claude-3-haiku")
    print(client.get_response("Hello, how are you?"))