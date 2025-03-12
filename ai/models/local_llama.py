from .base import AIModelInterface

class LocalLlamaModel(AIModelInterface):
    def __init__(self):
        self.configured = False
    
    @classmethod
    def configure(cls, config: dict):
        # Implementation for local model setup
        pass
    
    def get_caption_from_image(self, image_bytes: bytes) -> str:
        # Implementation for local model caption generation
        return "A generated caption from local model"
    
    def generate_hashtags(self, caption: str, count: int = 5) -> List[str]:
        # Implementation for local hashtag generation
        return ["hashtag1", "hashtag2", "hashtag3"]