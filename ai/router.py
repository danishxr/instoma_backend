"""
This file is the entry point for the AI service.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Union, List
import logging
from pydantic import BaseModel
from fastapi import HTTPException
import base64
import re
from .model_factory import get_vision_model, configure_model_by_provider
from .config import AI_CONFIG
from .agents.instagram_tools.insta_agent import analyze_instagram_users

# Set up logging
logger = logging.getLogger("ai-router")

airouter = APIRouter(prefix="/ai", tags=["AI Services"])

# Initialize vision model using the factory
try:
    vision_model = get_vision_model()
except Exception as e:
    logger.error(f"Failed to initialize vision model: {str(e)}")
    vision_model = None


@airouter.post("/configure-model")
async def configure_model(provider: str, config: dict):
    """
    Endpoint to reconfigure the model with a different provider.
    """
    global vision_model

    try:
        new_model = configure_model_by_provider(provider, config)
        if new_model:
            vision_model = new_model
            return {"status": "success", "message": f"Model {provider} configured"}
        else:
            return {"status": "error", "message": f"Unknown provider: {provider}"}
    except Exception as e:
        logger.error(f"Model configuration failed: {str(e)}")
        return {"status": "error", "message": str(e)}


# Add request model
class ImageRequest(BaseModel):
    imageUrl: str

# Update the endpoint
@airouter.post("/generate-caption-hashtags")
async def generate_caption_hashtags(request: ImageRequest) -> List[Dict[str, Union[str, List[str]]]]:
    try:
        # Extract base64 data from URL
        image_data = request.imageUrl.split(",")[1]
        
        # Add padding if needed
        padding = '=' * (-len(image_data) % 4)
        image_bytes = base64.b64decode(image_data + padding)
        
        result = vision_model.get_caption_from_image(image_bytes)
        return result
    except (IndexError, ValueError) as e:
        raise HTTPException(status_code=400, detail="Invalid image format")
    except Exception as e:
        logger.error(f"Caption generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Caption generation error")

# Define request model for Instagram user analysis
class InstagramAnalysisRequest(BaseModel):
    usernames: List[str]
    max_iterations: int = 10
    verbose: bool = False

# Add new endpoint for Instagram user analysis
@airouter.post("/analyze-instagram-users")
async def analyze_users(request: InstagramAnalysisRequest) -> Dict[str, Union[bool, str, List]]:
    """
    Endpoint to analyze Instagram users and rank them based on metrics.
    """
    try:
        logger.info(f"Analyzing Instagram users: {request.usernames}")
        
        # Call the analyze_instagram_users function from insta_agent.py
        ranked_users = analyze_instagram_users(
            usernames=request.usernames,
            max_iterations=request.max_iterations,
            verbose=request.verbose
        )
        
        return {
            "success": True,
            "message": f"Successfully analyzed {len(ranked_users)} users",
            "ranked_users": ranked_users
        }
    except Exception as e:
        logger.error(f"Instagram user analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Helper function to validate image data
def decode_base64_image(data_url: str) -> bytes:
    try:
        # Validate data URL format
        if not data_url.startswith("data:image/"):
            raise ValueError("Invalid media type")
            
        header, data = data_url.split(",", 1)
        media_type = header.split(":")[1].split(";")[0]
        
        # Decode with padding
        padding = '=' * (-len(data) % 4)
        return base64.b64decode(data + padding)
    except Exception as e:
        raise ValueError(f"Invalid image data: {str(e)}")
