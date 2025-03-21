from .base import AIModelInterface
import requests
import logging
import base64
from PIL import Image
import io
import re


class VisionLlamaModel(AIModelInterface):
    def __init__(self):
        self.logger = logging.getLogger("vision-llama")
        self.configured = False
        self.ollama_url = None
        self.model_name = None

    @classmethod
    def configure(cls, config: dict):
        try:
            # Store in class variables
            cls.ollama_url = config["local"]["ollama_url"]
            cls.model_name = config["local"]["vision_model_path"]
            cls.configured = True
            logging.info("Vision model configuration loaded successfully")
            return cls  # Return class for method chaining
        except Exception as e:
            logging.error(f"Vision model config failed: {str(e)}")
            raise

    @staticmethod
    def find_hashtag_pattern(text):
        pattern = re.compile(r"\#\w+")
        match = pattern.findall(text)
        match_list = list(set(match))
        return match_list

    @staticmethod
    def find_caption_pattern(text):
        breakpoint()
        cap_pattern = re.compile(r"[cC]aption:\n*.+\.")
        cap_match = cap_pattern.findall(text)
        return cap_match

    def get_caption_from_image(self, image_bytes: bytes) -> str:
        """
        Method to generate the caption and hashtad for the given image.
        """
        try:
            # Access class variables instead of instance variables
            if not self.__class__.configured:
                raise ValueError("Model not configured. Call configure() first.")

            # Convert image to PIL Image
            img = Image.open(io.BytesIO(image_bytes))

            # Resize image if it's too large
            max_size = 1024
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.LANCZOS)

            # Remove breakpoint
            # Convert to RGB if image has alpha channel
            if img.mode in ("RGBA", "LA"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background

            # Save to bytes buffer
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            img_bytes = buffer.getvalue()

            # Encode as base64
            encoded_image = base64.b64encode(img_bytes).decode("utf-8")

            # Create vision prompt
            prompt = """[INST] 
            Analyze this image and generate an engaging Instagram caption and hashtags, the output should be in a json format.
            Format:
            {'caption':<caption>,
            'hashtags':<hashtags>}
            There should not be any additional strings or characters.
            Also follow these rules:
            - Use emojis where appropriate
            - Keep under 200 characters
            - Include a call-to-action
            - Make it brand-friendly
            [/INST]"""

            # Create request payload
            payload = {
                "model": self.__class__.model_name,  # Use class variable
                "prompt": prompt,
                "images": [encoded_image],
                "stream": False,
            }

            # Send request to Ollama API
            endpoint = f"{self.__class__.ollama_url}/api/generate"  # Use class variable
            response = requests.post(endpoint, json=payload)

            response_hashtags = self.find_hashtag_pattern(response.json()["response"])
            response_caption = self.find_caption_pattern(response.json()["response"])

            final_result = {"caption": response_caption, "hashtags": response_hashtags}

            if response.status_code == 200:

                return final_result
            else:
                raise Exception(f"API Error: {response.status_code}, {response.text}")

        except Exception as e:
            self.logger.error(f"Caption generation failed: {str(e)}")
            return "Could not generate caption"

    def generate_hashtags(self, caption: str, count: int = 5) -> list:
        raise NotImplementedError("Vision model doesn't handle hashtag generation")


if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from ai.config import AI_CONFIG

    # Initialize and configure model
    model = VisionLlamaModel()
    model.configure(AI_CONFIG)

    # Test directory with images
    test_image_dir = (
        "/Users/dan/playground/insta_automation_plugin/myplugin/backend/test_images/"
    )

    # Process each image in the directory
    for image_file in os.listdir(test_image_dir):
        if image_file.lower().endswith((".png", ".jpg", ".jpeg")):
            image_path = os.path.join(test_image_dir, image_file)

            # Read image bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            # Generate caption
            # Start time
            import time

            start_time = time.time()
            print(f"\nProcessing image: {image_file}")
            print("-" * 50)
            caption = model.get_caption_from_image(image_bytes)
            print(f"Generated caption: {caption}")
            print("-" * 50)
            end_time = time.time()
            # Calculate elapsed time
            elapsed_time = end_time - start_time
            print(f"Elapsed time for cpation: {elapsed_time:.2f} seconds")
