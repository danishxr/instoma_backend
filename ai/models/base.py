from abc import ABC, abstractmethod
from typing import List

class AIModelInterface(ABC):
    @classmethod
    @abstractmethod
    def configure(cls, config: dict):
        """Initialize model with configuration"""
        pass
    
    @abstractmethod
    def get_caption_from_image(self, image_bytes: bytes) -> str:
        """Generate caption from image bytes"""
        pass
    
    @abstractmethod
    def generate_hashtags(self, caption: str, count: int = 5) -> List[str]:
        """Generate relevant hashtags based on caption"""
        pass