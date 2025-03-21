from .base import AIModelInterface
import logging
import os
import json
import re
from PIL import Image
import io
from google import genai
from typing import List, Dict, Any, Union

class GoogleGeminiModel(AIModelInterface):
    """
    AI model implementation using Google's Gemini API for generating
    captions and hashtags for Instagram posts.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("google-gemini")
        self.configured = False
        self.client = None
        self.model_name = None
    
    @classmethod
    def configure(cls, config: dict):
        """Configure the Google Gemini client with API key from config"""
        try:
            api_key = config.get("google", {}).get("api_key") or os.getenv("GOOGLE_API_KEY")
            
            if not api_key:
                raise ValueError("Google API key not found in config or environment")
                
            cls.client = genai.Client(api_key=api_key)
            cls.model_name = config.get("google", {}).get("model_name", "gemini-2.0-flash")
            cls.configured = True
            logging.info(f"Google Gemini model configured successfully: {cls.model_name}")
            return cls
        except Exception as e:
            logging.error(f"Google Gemini configuration failed: {str(e)}")
            raise
    
    def get_caption_from_image(self, image_bytes: bytes) -> List[Dict[str, Union[str, List[str]]]]:
        try:
            if not self.__class__.configured or not self.__class__.client:
                raise ValueError("Model not configured. Call configure() first")
    
            num_variations = 3  # Make this configurable later
            img = Image.open(io.BytesIO(image_bytes))
            
            response = self.__class__.client.models.generate_content(
                model=self.__class__.model_name,
                contents=[
                    f"""Generate {num_variations} Instagram caption variations with hashtags. Format:
                    {{
                        "variations": [
                            {{"caption": "caption1", "hashtags": ["tag1", "tag2"]}},
                            {{"caption": "caption2", "hashtags": ["tag3", "tag4"]}},
                            {{"caption": "caption3", "hashtags": ["tag5", "tag6"]}}
                        ]
                    }}""",
                    img,
                ],
            )
    
            try:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    return result.get('variations', [])
            except json.JSONDecodeError:
                return self._fallback_variation_generation(response.text, num_variations)
    
        except Exception as e:
            self.logger.error(f"Caption generation failed: {str(e)}")
            return [{"caption": "Could not generate caption", "hashtags": []}]
    
    def _fallback_variation_generation(self, text: str, num_variations: int) -> List[Dict[str, Any]]:
        variations = []
        for i in range(1, num_variations+1):
            caption = self._extract_caption(text + f"\nVariation {i}:")
            hashtags = self._extract_hashtags(text)[:5]
            variations.append({
                "caption": caption,
                "hashtags": hashtags
            })
        return variations
    
    def generate_hashtags(self, caption: str, count: int = 5) -> List[str]:
        """
        Generate hashtags based on a caption using Google Gemini.
        
        Args:
            caption: The caption text
            count: Number of hashtags to generate
            
        Returns:
            List of hashtags
        """
        try:
            if not self.__class__.configured or not self.__class__.client:
                raise ValueError("Model not configured. Call configure() first.")
            
            prompt = f"""Generate {count} relevant Instagram hashtags for this caption:
            "{caption}"
            
            Rules:
            - Mix popular and niche tags
            - Include at least 2 community tags
            - No duplicates
            - Max 25 characters per tag
            - Return only the hashtags, no explanations
            """
            
            response = self.__class__.client.models.generate_content(
                model=self.__class__.model_name,
                contents=prompt
            )
            
            # Extract hashtags from response
            hashtags = self._extract_hashtags(response.text)
            
            # Ensure we have the requested number of hashtags
            if len(hashtags) < count:
                # Add some generic hashtags if we don't have enough
                generic_tags = ["instagram", "social", "photooftheday", "picoftheday", "instagood"]
                hashtags.extend(generic_tags[:(count - len(hashtags))])
            
            return hashtags[:count]
            
        except Exception as e:
            self.logger.error(f"Hashtag generation failed: {str(e)}")
            return ["instagram", "social", "photooftheday"][:count]
    
    def _extract_caption(self, text: str) -> str:
        """Extract caption from text response"""
        caption_pattern = re.compile(r'caption["\s:]+([^"#]+)', re.IGNORECASE)
        match = caption_pattern.search(text)
        if match:
            return match.group(1).strip()
        return text.split("hashtags")[0] if "hashtags" in text else text
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text response"""
        # Look for hashtags in the format #word
        hashtag_pattern = re.compile(r'#\w+')
        hashtags = hashtag_pattern.findall(text)
        
        # If no hashtags found with #, try to extract from a list
        if not hashtags:
            # Try to find hashtags in a list format
            list_pattern = re.compile(r'hashtags["\s:]+\[(.*?)\]', re.IGNORECASE | re.DOTALL)
            match = list_pattern.search(text)
            if match:
                items = match.group(1).split(',')
                hashtags = [item.strip().strip('"\'').strip() for item in items]
                # Add # if missing
                hashtags = [f"#{tag}" if not tag.startswith('#') else tag for tag in hashtags]
        
        return list(set(hashtags))  # Remove duplicates


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from ai.config import AI_CONFIG
    
    # Update AI_CONFIG with Google settings if not already present
    if "google" not in AI_CONFIG:
        AI_CONFIG["google"] = {
            "api_key": os.getenv("GOOGLE_API_KEY"),
            "model_name": "gemini-2.0-flash"
        }
    
    # Initialize and configure model
    model = GoogleGeminiModel()
    model.configure(AI_CONFIG)
    
    # Test directory with images
    test_image_dir = "/Users/dan/playground/insta_automation_plugin/myplugin/backend/test_images/"
    
    # Process each image in the directory
    for image_file in os.listdir(test_image_dir):
        if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(test_image_dir, image_file)
            
            # Read image bytes
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Generate caption and hashtags
            import time
            start_time = time.time()
            print(f"\nProcessing image: {image_file}")
            print("-" * 50)
            result = model.get_caption_from_image(image_bytes)
            print(f"Generated caption: {result.get('caption', 'No caption')}")
            print(f"Generated hashtags: {result.get('hashtags', [])}")
            print("-" * 50)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Elapsed time: {elapsed_time:.2f} seconds")