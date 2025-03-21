from .base import AIModelInterface
from llama_cpp import Llama
import logging
import base64
from typing import List, Dict, Union

class VisionLlamaModel(AIModelInterface):
    def __init__(self):
        self.model = None
        self.logger = logging.getLogger("vision-llama")
        self.configured = False

    @classmethod
    def configure(cls, config: dict):
        try:
            breakpoint()
            cls.model = Llama(
                model_path=config["local"]["vision_model_path"],
                n_ctx=2048,
                n_threads=4,
                verbose=False,
            )
            cls.configured = True
            logging.info("Vision model loaded successfully")
        except Exception as e:
            logging.error(f"Vision model config failed: {str(e)}")
            raise

    def get_caption_from_image(self, image_bytes: bytes) -> List[Dict[str, Union[str, List[str]]]]:
        try:
            b64_image = base64.b64encode(image_bytes).decode('utf-8')
            prompt = """[INST] 
            Generate 3 Instagram caption variations with hashtags. Format:
            Variation 1: [Caption] [Hashtags]
            Variation 2: [Caption] [Hashtags]
            Variation 3: [Caption] [Hashtags]
            [/INST]"""

            response = self.model.create_chat_completion(
                messages=[{"role": "user", "content": f"Image data: [img:{b64_image}]\n{prompt}"}]
            )
            
            # Add parsing logic similar to GoogleGeminiModel
            return self._parse_llama_response(response['choices'][0]['message']['content'])

        except Exception as e:
            self.logger.error(f"Caption generation failed: {str(e)}")
            return [{"caption": "Could not generate caption", "hashtags": []}]

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
    test_image_dir = "/Users/dan/playground/insta_automation_plugin/myplugin/backend/test_images"

    # Process each image in the directory
    for image_file in os.listdir(test_image_dir):
        if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(test_image_dir, image_file)

            # Read image bytes
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            # Generate caption
            print(f"\nProcessing image: {image_file}")
            print("-" * 50)
            caption = model.get_caption_from_image(image_bytes)
            print(f"Generated caption: {caption}")
            print("-" * 50)
