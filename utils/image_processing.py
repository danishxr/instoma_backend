from PIL import Image
import logging

logger = logging.getLogger("image-utils")

def resize_image_for_instagram(image):
    """
    Resize image to Instagram's standard size (1080x1080) if larger,
    otherwise keep original dimensions
    """
    INSTAGRAM_STANDARD_SIZE = (1080, 1080)
    width, height = image.size
    
    if width <= INSTAGRAM_STANDARD_SIZE[0] and height <= INSTAGRAM_STANDARD_SIZE[1]:
        return image
        
    if width > height:
        new_width = INSTAGRAM_STANDARD_SIZE[0]
        new_height = int(height * (new_width / width))
    else:
        new_height = INSTAGRAM_STANDARD_SIZE[1]
        new_width = int(width * (new_height / height))
    
    return image.resize((new_width, new_height), Image.LANCZOS)