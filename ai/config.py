import os
from dotenv import load_dotenv



AI_CONFIG = {
    "model_provider": os.getenv("AI_MODEL_PROVIDER", "local"),
    "local": {
        "vision_model_path": os.getenv("VISION_MODEL_PATH", "llama3.2-vision:latest"),
        "text_model_path": os.getenv("TEXT_MODEL_PATH", "models/llama3.1.gguf"),
        "temperature": 0.7,
        "ollama_url": os.getenv("OLLAMA_URL", "http://localhost:11434")  # Added this line
    },
    "aws": {
        "access_key": os.getenv("AWS_ACCESS_KEY"),
        "secret_key": os.getenv("AWS_SECRET_KEY"),
        "region": os.getenv("AWS_REGION"),
    },
    "azure": {
        "api_key": os.getenv("AZURE_API_KEY"),
        "endpoint": os.getenv("AZURE_ENDPOINT"),
    },
    # Add this to your existing AI_CONFIG dictionary
    "google": {
        "api_key": os.getenv("GOOGLE_API_KEY"),
        "model_name": os.getenv("GOOGLE_MODEL_NAME", "gemini-2.0-flash"),
    },
    "caption_settings":{
        "num_variations": 3,
    }

}
