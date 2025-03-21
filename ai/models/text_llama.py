from .base import AIModelInterface
from llama_cpp import Llama
import logging

class TextLlamaModel(AIModelInterface):
    def __init__(self):
        self.model = None
        self.logger = logging.getLogger("text-llama")
        self.configured = False

    @classmethod
    def configure(cls, config: dict):
        try:
            cls.model = Llama(
                model_path=config["local"]["text_model_path"],
                n_ctx=1024,
                n_threads=4,
                verbose=False
            )
            cls.configured = True
            logging.info("Text model loaded successfully")
        except Exception as e:
            logging.error(f"Text model config failed: {str(e)}")
            raise

    def generate_hashtags(self, caption: str, count: int = 5) -> list:
        try:
            prompt = f"""[INST]
            Generate {count} relevant Instagram hashtags based on this caption:
            {caption}
            
            Rules:
            - Mix popular and niche tags
            - Include at least 2 community tags
            - No duplicates
            - Max 25 characters per tag
            [/INST]"""
            
            response = self.model.create_chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            return response['choices'][0]['message']['content'].split()[:count]
            
        except Exception as e:
            self.logger.error(f"Hashtag generation failed: {str(e)}")
            return ["social", "instagram"]

    def get_caption_from_image(self, image_bytes: bytes) -> str:
        raise NotImplementedError("Text model doesn't handle image processing")