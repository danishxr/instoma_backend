import os
from dotenv import load_dotenv

load_dotenv()

AI_CONFIG = {
    "model_provider": os.getenv("AI_MODEL_PROVIDER", "local"),
    "local": {
        "model_path": os.getenv("LOCAL_MODEL_PATH", "models/llama-2-7b-chat.Q4_K_M.gguf"),
        "temperature": 0.7
    },
    "aws": {
        "access_key": os.getenv("AWS_ACCESS_KEY"),
        "secret_key": os.getenv("AWS_SECRET_KEY"),
        "region": os.getenv("AWS_REGION")
    },
    "azure": {
        "api_key": os.getenv("AZURE_API_KEY"),
        "endpoint": os.getenv("AZURE_ENDPOINT")
    }
}