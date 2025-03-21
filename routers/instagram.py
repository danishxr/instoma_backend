from fastapi import APIRouter, Response, status
from social.instagram import InstagramClient
from utils.image_processing import resize_image_for_instagram
from pydantic import BaseModel
from typing import List
import base64
import io
from PIL import Image
import time
import os

router = APIRouter(prefix="/instagram", tags=["Instagram"])
client = InstagramClient()

class InstagramPostRequest(BaseModel):
    imageUrl: str
    caption: str
    hashtags: List[str]

@router.post("/post", status_code=status.HTTP_200_OK)
async def post_to_instagram(request: InstagramPostRequest, response: Response):
    try:
        # Image processing logic
        image_data = request.imageUrl.split("base64,")[1] if "base64," in request.imageUrl else request.imageUrl
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        image = resize_image_for_instagram(image)
        
        # Save temp file
        temp_path = f"temp_ig_{int(time.time())}.jpg"
        image.save(temp_path, quality=95)
        
        # Post to Instagram
        media = client.send_post(temp_path, f"{request.caption} {' '.join(request.hashtags)}")
        
        return {
            "success": True,
            "media_id": media.id,
            "media_url": f"https://www.instagram.com/p/{media.code}/"
        }
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"success": False, "message": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/account-info")
async def get_account_info(response: Response):
    try:
        user_info = client.client.user_info(client.client.user_id)
        return {
            "username": user_info.username,
            "follower_count": user_info.follower_count,
            "media_count": user_info.media_count
        }
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"success": False, "message": str(e)}