import base64
import requests
import re
import os
from urllib.parse import urlparse
import mimetypes

from .base import Pipeline

from openai import OpenAI

client = OpenAI()


class GPTVVisionAPIPipeline(Pipeline):
    def __init__(self):
        try:
            self.api_key = os.environ["OPENAI_API_KEY"]
        except KeyError:
            raise KeyError(
                "Please set your OpenAI API key in the environment variable `OPENAI_API_KEY`"
            )
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        self.api_url = "https://api.openai.com/v1/chat/completions"

    @staticmethod
    def is_base64(s):
        try:
            return base64.b64encode(base64.b64decode(s)).decode("utf-8") == s
        except Exception:
            return False

    @staticmethod
    def is_url(s):
        # Ensure the input is a string
        if not isinstance(s, str):
            return False
        try:
            result = urlparse(s)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    @staticmethod
    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def process_image(self, image_input):
        if self.is_url(image_input):
            image_content = {"type": "image_url", "image_url": {"url": image_input}}
        elif self.is_base64(image_input):
            mime_type, _ = mimetypes.guess_type(image_input[:30])
            # Guess mime type from base64
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_input}"},
            }
        else:
            try:
                base64_image = self.encode_image(image_input)
                mime_type, _ = mimetypes.guess_type(image_input)
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                }
            except FileNotFoundError:
                print(f"Error: File not found - {image_input}")
                return
        return image_content

    def generate_caption(self, text, image_input):
        image_content = self.process_image()
        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": text}, image_content],
                }
            ],
            "max_tokens": 300,
        }

        response = requests.post(self.api_url, headers=self.headers, json=payload)
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"Request failed: {e}")


if __name__ == "__main__":
    """
    python -m visualwebarena.evaluation_harness.vision.openai
    """
    image_src = [
        "media/homepage_demo.png",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
    ][0]
    prompt = "Describe the element and a detailed summary of what's in this webpage?"

    def example():
        pipeline = GPTVVisionAPIPipeline()
        caption = pipeline.generate_caption(prompt, image_src)
        return caption

    print(example())
