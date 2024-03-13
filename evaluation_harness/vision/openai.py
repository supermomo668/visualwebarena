import base64
import requests
import re
import os
import io
from urllib.parse import urlparse
import mimetypes

from openai import OpenAI
from PIL import Image

from .base import Pipeline

client = OpenAI()


class GPTVVisionAPIPipeline(Pipeline):
    def __init__(self, model="gpt-4-vision-preview", max_tokens=300):
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
        self.model="gpt-4-vision-preview"
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
    def encode_image(self, image_input):
        if isinstance(image_input, str) and (self.is_url(image_input) or self.is_base64(image_input)):
            return image_input
        elif isinstance(image_input, Image.Image):
            buffered = io.BytesIO()
            image_input.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
        else:
            raise ValueError("Unsupported image input type")

    def process_image(self, text, image_input):
        if not isinstance(images, list):
            images = [images]
            
        image_contents = []
        for image in images:
            encoded_image = self.encode_image(image)
            if self.is_url(encoded_image):
                image_content = {"type": "image_url", "image_url": {"url": encoded_image}}
            else:
                mime_type, _ = mimetypes.guess_type(image[:30]) if isinstance(image, str) else ("image/jpeg", None)
                image_content = {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"}}
            image_contents.append(image_content)
        return image_contents
    
    def generate_caption(self, text, images):
        image_content = self.process_image(
            text, images)
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": image_content}],
            "max_tokens": self.max_tokens
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
