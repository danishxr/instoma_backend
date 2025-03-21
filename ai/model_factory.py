"""
Factory module for creating and configuring AI models based on environment settings.
"""
import os
import logging
from typing import Dict, Any, Optional

# Import all model implementations
from .models.vision_llama import VisionLlamaModel
from .models.vision_trial_llama import VisionLlamaModel as VisionTrialLlamaModel
from .models.google_gemini import GoogleGeminiModel
from .models.base import AIModelInterface
from .config import AI_CONFIG

# Set up logging
logger = logging.getLogger("model-factory")

def get_vision_model() -> AIModelInterface:
    """
    Factory function to create and configure the appropriate vision model
    based on the MODEL_SWITCH environment variable.
    
    Returns:
        Configured vision model instance
    """
    # Get model type from environment variable
    model_switch = os.getenv("MODEL_SWITCH", "ollama").lower()
    
    try:
        # Select the appropriate model class
        if model_switch == "ollama":
            logger.info("Using Ollama vision model")
            model = VisionTrialLlamaModel()
        elif model_switch == "llama":
            logger.info("Using Llama.cpp vision model")
            model = VisionLlamaModel()
        elif model_switch == "gemini":
            logger.info("Using Google Gemini vision model")
            model = GoogleGeminiModel()
        else:
            logger.warning(f"Unknown model type: {model_switch}, defaulting to Ollama")
            model = VisionTrialLlamaModel()
        
        # Configure the selected model
        model.configure(AI_CONFIG)
        logger.info(f"Vision model {model_switch} configured successfully")
        return model
        
    except Exception as e:
        logger.error(f"Failed to initialize vision model: {str(e)}")
        raise

def configure_model_by_provider(provider: str, config: Dict[str, Any]) -> Optional[AIModelInterface]:
    """
    Configure a model based on the specified provider.
    
    Args:
        provider: The model provider name
        config: Configuration dictionary
        
    Returns:
        Configured model instance or None if provider is unknown
    """
    try:
        if provider == "ollama":
            model = VisionTrialLlamaModel()
        elif provider == "llama":
            model = VisionLlamaModel()
        elif provider == "gemini":
            model = GoogleGeminiModel()
        else:
            logger.error(f"Unknown provider: {provider}")
            return None
        
        model.configure(config)
        logger.info(f"Model {provider} configured successfully")
        return model
    except Exception as e:
        logger.error(f"Model configuration failed: {str(e)}")
        raise