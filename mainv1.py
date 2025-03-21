from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from routers.instagram import router as instagram_router
from ai.router import airouter as ai_router
from utils.logger import LoggingConfigurator

# Load environment variables from .env file
cwd = os.getcwd()
load_dotenv(os.path.join(cwd, ".env"))

# Initialize logging first
LoggingConfigurator.configure_logging()

app = FastAPI(title="Social Media Automation API")

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(instagram_router, prefix="/api")
# include ai routers
app.include_router(ai_router, prefix="/ai")
# Include routers
app.include_router(instagram_router)
# Add Threads and Facebook routers later

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mainv1:app", host="0.0.0.0", port=8188, reload=True)
