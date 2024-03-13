import base64
import requests
import re

from typing import  str, bool
from .base import Pipeline

class GPTVVisionAPIPipeline(Pipeline):
    def __init__(
        self, api_key: str, model: str = "gpt-4-vision-preview"):
        self.api_key = api_key
        self.model = model

    def encode_image(self, image_path: str) -> str:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise IOError(f"Failed to encode image: {e}")

    def is_base64(self, s: str) -> bool:
        try:
            if base64.b64encode(base64.b64decode(s)).decode('utf-8') == s:
                return True
            return False
        except Exception:
            return False

    def is_url(self, s: str) -> bool:
        return re.match(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', s) is not None

    def generate_caption(self, text: str, image_input: str, max_token=300):
        if self.is_url(image_input):
            image_content = {"type": "image_url", "image_url": {"url": image_input}}
        elif self.is_base64(image_input):
            image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_input}"}}
        else:
            # Assuming the input is a file path
            base64_image = self.encode_image(image_input)
            image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        image_content
                    ]
                }
            ],
            "max_tokens": max_token
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        try:
            response.raise_for_status()
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        except requests.exceptions.HTTPError as e:
            raise Exception(f"API request failed: {e}")

if __name__ == "__main__":
    """
    python -m visualwebarena.evaluation_harness.vision.openai
    """
    prompt = "What's in this image?"
    def example():
        pipeline = GPTVVisionAPIPipeline()
        caption = pipeline.generate_caption(
            prompt, "path/to/your/image.jpg")
        return caption
    print(example())