from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import base64
import os
import io
import logging
import time
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError, ClientLoginRequired, ClientConnectionError
from PIL import Image
from ai.router import router as ai_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("instagram_api.log")
    ]
)
logger = logging.getLogger("instagram-api")

# Load environment variables
load_dotenv(os.path.join(os.getcwd(), ".env"))
logger.info(f"Environment loaded from: {os.path.join(os.getcwd(), '.env')}")

app = FastAPI(title="Instagram Automation API")
app.include_router(ai_router)  # Add this line after CORS configuration

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your SvelteKit dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InstagramPostRequest(BaseModel):
    imageUrl: str
    caption: str
    hashtags: List[str]

def resize_image_for_instagram(image):
    """
    Resize image to Instagram's standard size (1080x1080) if larger,
    otherwise keep original dimensions
    """
    INSTAGRAM_STANDARD_SIZE = (1080, 1080)
    width, height = image.size
    logger.debug(f"Original image dimensions: {width}x{height}")
    
    # If image is smaller than Instagram standard size, keep original dimensions
    if width <= INSTAGRAM_STANDARD_SIZE[0] and height <= INSTAGRAM_STANDARD_SIZE[1]:
        logger.debug("Image is smaller than Instagram standard size, keeping original dimensions")
        return image
    
    # Calculate new dimensions while maintaining aspect ratio
    if width > height:
        new_width = INSTAGRAM_STANDARD_SIZE[0]
        new_height = int(height * (new_width / width))
    else:
        new_height = INSTAGRAM_STANDARD_SIZE[1]
        new_width = int(width * (new_height / height))
    
    logger.debug(f"Resizing image to: {new_width}x{new_height}")
    
    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    return resized_image

# Create a client instance
instagram_client = None

def get_instagram_client():
    """
    Get or create an Instagram client instance
    """
    global instagram_client
    
    if instagram_client is not None:
        # Check if client is still logged in
        try:
            instagram_client.get_timeline_feed()
            logger.debug("Reusing existing Instagram client")
            return instagram_client
        except (LoginRequired, ClientLoginRequired):
            logger.info("Session expired, creating new client")
            instagram_client = None
    
    # Create new client
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        logger.error("Instagram credentials not configured")
        raise ValueError("Instagram credentials not configured")
    
    client = Client()
    
    # Try to load session from file
    session_file = f"{username}_session.json"
    if os.path.exists(session_file):
        try:
            logger.info(f"Loading session from {session_file}")
            client.load_settings(session_file)
            client.login(username, password)
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
            # If loading fails, login normally
            client.login(username, password)
            client.dump_settings(session_file)
    else:
        # Login and save session
        logger.info("Creating new Instagram session")
        client.login(username, password)
        client.dump_settings(session_file)
    
    instagram_client = client
    return client

@app.post("/api/instagram/post", status_code=status.HTTP_200_OK)
async def post_to_instagram(request: InstagramPostRequest, response: Response):
    try:
        logger.info("Processing Instagram post request")
        
        # Process the base64 image
        logger.debug("Processing image data")
        image_data = request.imageUrl

        # Remove the data URL prefix if present
        if "base64," in image_data:
            logger.debug("Removing data URL prefix from image")
            image_data = image_data.split("base64,")[1]

        try:
            # Decode the base64 image
            logger.debug("Decoding base64 image")
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            logger.debug(f"Image format: {image.format}, Mode: {image.mode}")
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize image if needed
            logger.debug("Resizing image for Instagram")
            image = resize_image_for_instagram(image)
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"success": False, "message": f"Invalid image data: {str(e)}"}

        # Save the image temporarily
        temp_image_path = f"temp_instagram_image_{int(time.time())}.jpg"
        logger.debug(f"Saving temporary image to: {temp_image_path}")
        image.save(temp_image_path, quality=95)

        # Combine caption and hashtags
        full_caption = f"{request.caption} {' '.join(request.hashtags)}"
        logger.debug(f"Caption: {request.caption}")
        logger.debug(f"Hashtags: {request.hashtags}")
        logger.debug(f"Full caption length: {len(full_caption)} characters")

        try:
            # Get Instagram client
            client = get_instagram_client()
            
            # Upload the photo
            logger.info("Uploading photo to Instagram")
            
            # Upload as a feed post
            media = client.photo_upload(
                path=temp_image_path,
                caption=full_caption
            )
            
            logger.info(f"Photo uploaded successfully with media ID: {media.id}")
            
        except ClientLoginRequired as e:
            logger.error(f"Instagram login required: {str(e)}", exc_info=True)
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return {"success": False, "message": "Instagram login required. Please check your credentials."}
        except ClientError as e:
            logger.error(f"Instagram client error: {str(e)}", exc_info=True)
            response.status_code = status.HTTP_502_BAD_GATEWAY
            return {"success": False, "message": f"Instagram API error: {str(e)}"}
        except ClientConnectionError as e:
            logger.error(f"Instagram connection error: {str(e)}", exc_info=True)
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"success": False, "message": "Could not connect to Instagram. Please try again later."}
        except Exception as e:
            logger.error(f"Instagram upload error: {str(e)}", exc_info=True)
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return {"success": False, "message": f"Error uploading to Instagram: {str(e)}"}
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_image_path):
                logger.debug(f"Removing temporary file: {temp_image_path}")
                os.remove(temp_image_path)

        logger.info("Instagram post completed successfully")
        return {
            "success": True, 
            "message": "Image posted successfully to Instagram",
            "media_id": media.id,
            "media_url": f"https://www.instagram.com/p/{media.code}/"
        }

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"success": False, "message": f"Server error: {str(e)}"}

@app.get("/api/instagram/account-info")
async def get_account_info(response: Response):
    """Get information about the logged-in Instagram account"""
    try:
        client = get_instagram_client()
        user_id = client.user_id
        user_info = client.user_info(user_id)
        
        return {
            "success": True,
            "username": user_info.username,
            "full_name": user_info.full_name,
            "follower_count": user_info.follower_count,
            "following_count": user_info.following_count,
            "media_count": user_info.media_count,
            "profile_pic_url": user_info.profile_pic_url
        }
    except Exception as e:
        logger.error(f"Error getting account info: {str(e)}", exc_info=True)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"success": False, "message": f"Error getting account info: {str(e)}"}

@app.get("/health")
async def health_check():
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting Instagram Automation API server")
    import uvicorn
    uvicorn.run("mainv1:app", host="0.0.0.0", port=8188, reload=True)