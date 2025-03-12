from fastapi import APIRouter, UploadFile, File
from ..models import LocalLlamaModel  # Default implementation

router = APIRouter(prefix="/ai", tags=["AI Services"])

# Initialize with default model
current_model = LocalLlamaModel()

@router.post("/configure-model")
async def configure_model(provider: str, config: dict):
    global current_model
    # Add logic to switch between different model providers
    # Example: if provider == "azure": ...
    return {"status": "Model configured"}

@router.post("/generate-caption")
async def generate_caption(image: UploadFile = File(...)):
    image_bytes = await image.read()
    caption = current_model.get_caption_from_image(image_bytes)
    return {"caption": caption}

@router.post("/generate-hashtags")
async def generate_hashtags(caption: str, count: int = 5):
    hashtags = current_model.generate_hashtags(caption, count)
    return {"hashtags": hashtags}