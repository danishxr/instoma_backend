import os
import logging
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError, ClientLoginRequired

class InstagramClient:
    def __init__(self):
        self.client = None
        self.logger = logging.getLogger("instagram-client")
        self._load_credentials()
        
    def _load_credentials(self):
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        
        if not self.username or not self.password:
            raise ValueError("Instagram credentials not found in environment")

    def configure(self):
        """Initialize or refresh Instagram client connection"""
        try:
            if self.client and self._validate_session():
                return True
                
            self.client = Client()
            session_file = f"{self.username}_session.json"
            
            if os.path.exists(session_file):
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password)
            else:
                self.client.login(self.username, self.password)
                self.client.dump_settings(session_file)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration failed: {str(e)}")
            return False

    def _validate_session(self):
        try:
            self.client.get_timeline_feed()
            return True
        except (LoginRequired, ClientLoginRequired):
            return False

    def send_post(self, image_path: str, caption: str):
        """Publish post to Instagram feed"""
        if not self.configure():
            raise ConnectionError("Failed to establish Instagram connection")
            
        try:
            return self.client.photo_upload(image_path, caption)
        except ClientError as e:
            self.logger.error(f"Post failed: {str(e)}")
            raise

    def schedule_post(self, image_path: str, caption: str, schedule_time: int):
        """Schedule post for future publishing"""
        # Implementation would use background task scheduler
        pass

    def get_likes(self, media_id: str):
        """Get likes for a specific post"""
        if not self.configure():
            raise ConnectionError("Instagram connection not available")
            
        try:
            return self.client.media_likers(media_id)
        except ClientError as e:
            self.logger.error(f"Failed to get likes: {str(e)}")
            raise