import logging
import os
from dotenv import load_dotenv

class LoggingConfigurator:
    @staticmethod
    def configure_logging():
        """Configure logging with level from environment"""
        load_dotenv()  # Ensure environment variables are loaded
        
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        if log_level not in valid_levels:
            log_level = "INFO"
            
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("api.log")
            ]
        )
        logger = logging.getLogger("main")
        logger.info(f"Logging configured with level: {log_level}")
        return logger