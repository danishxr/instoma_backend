import os
import sys
import logging
import statistics
import time
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from instagrapi import Client
from instagrapi.types import Media, User
from typing import List, Dict, Any
from instagrapi.exceptions import LoginRequired, ClientError, ClientLoginRequired, UserNotFound

class InstagramTools:
    def __init__(self):
        self.client = None
        self.logger = logging.getLogger("instagram-tools")
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")

        if not self.username or not self.password:
            raise ValueError("Instagram credentials not found in environment")

        self.configure()

    def configure(self):
        """Initialize or refresh Instagram client connection"""
        try:
            self.client = Client()
            session_file = f"{self.username}_session.json"
            
            # Set custom device information to avoid detection
            self.client.set_device({
                "app_version": "269.0.0.18.75",
                "android_version": 26,
                "android_release": "8.0.0",
                "dpi": "480dpi",
                "resolution": "1080x1920",
                "manufacturer": "OnePlus",
                "device": "OnePlus6T",  # Changed from devitron to a real device name
                "model": "ONEPLUS A6013",  # Changed to actual model number
                "cpu": "qcom",
                "version_code": "314665256"
            })
            
            # Set user agent to a more common one
            self.client.user_agent = "Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; ONEPLUS A6013; OnePlus6T; qcom; en_US; 314665256)"
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1.0, 2.0))
            
            if os.path.exists(session_file):
                self.logger.info(f"Loading session from {session_file}")
                self.client.load_settings(session_file)
                
                # Check if session is valid
                if self._validate_session():
                    self.logger.info("Session is valid")
                    return self
                else:
                    self.logger.info("Session is invalid, performing full login")
            
            # Perform full login
            self.logger.info(f"Logging in as {self.username}")
            self.client.login(self.username, self.password)
            
            # Add delay after login
            time.sleep(random.uniform(1.0, 2.0))
            
            # Save the new session
            self.client.dump_settings(session_file)
            self.logger.info(f"Session saved to {session_file}")
            
            return self

        except Exception as e:
            self.logger.error(f"Configuration failed: {str(e)}")
            raise

    def _validate_session(self) -> bool:
        """Validate current session"""
        try:
            # Use a less intensive API call to validate session
            self.client.get_settings()
            return True
        except (LoginRequired, ClientLoginRequired):
            return False
        except Exception as e:
            self.logger.error(f"Session validation error: {str(e)}")
            return False

    def user_id_by_username(self, username: str) -> str:
        """Get user ID by username"""
        try:
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1.0, 2.0))
            return self.client.user_id_from_username(username)
        except (LoginRequired, ClientLoginRequired) as e:
            self.logger.warning(f"Login required, attempting to reconfigure: {str(e)}")
            self.configure()
            time.sleep(random.uniform(1.0, 2.0))
            return self.client.user_id_from_username(username)
        except ClientError as e:
            self.logger.error(f"Failed to get user ID: {str(e)}")
            raise
        except UserNotFound:
            self.logger.error(f"User '{username}' not found")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

    @staticmethod
    def convert_instagram_profile_pic_url(original_url):
        """
        Convert Instagram's complex CDN URL to a clean, direct image URL.
        
        Args:
            original_url (str): The original Instagram profile picture URL
        
        Returns:
            str: A cleaned, direct URL to the profile picture
        """
        # If the URL is already simple, return it directly
        if not original_url or 'instagram.com' not in original_url:
            return original_url
        
        try:
            # Remove all query parameters to get a clean URL
            clean_url = original_url.split('?')[0]
            
            # Optional: Replace resolution if you want a larger image
            # This replaces 's150x150' with a larger size or removes size constraint
            clean_url = clean_url.replace('s150x150', 's1080x1080')
            
            return clean_url
        
        except Exception as e:
            print(f"Error converting URL: {e}")
            return original_url

    def user_info_by_username(self, username: str) -> Dict[str, Any]:
        """Get user information by username"""
        try:
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1.0, 2.0))
            
            # Try to get user data
            user_data = self.client.user_info_by_username(username)
            user_id = self.user_id_by_username(username)
            
            # Clean the profile picture URL
            clean_profile_pic_url = self.convert_instagram_profile_pic_url(str(user_data.profile_pic_url))
            
            # Get engagement rate with error handling
            try:
                engagement_rate = self._calculate_engagement_rate(user_id)
            except Exception as e:
                self.logger.warning(f"Failed to calculate engagement rate: {str(e)}")
                engagement_rate = 0
            
            metrics = {
                "username": username,
                "followers_count": user_data.follower_count,
                "following_count": user_data.following_count,
                "media_count": user_data.media_count,
                "is_private": user_data.is_private,
                "is_verified": user_data.is_verified,
                "engagement_rate": engagement_rate,
                "profile_picture_url": clean_profile_pic_url,
            }
            return metrics
        except (LoginRequired, ClientLoginRequired) as e:
            self.logger.warning(f"Login required, attempting to reconfigure: {str(e)}")
            try:
                # Try to reconfigure and retry
                self.configure()
                time.sleep(random.uniform(2.0, 3.0))
                
                user_data = self.client.user_info_by_username(username)
                user_id = self.user_id_by_username(username)
                
                # Clean the profile picture URL
                clean_profile_pic_url = self.convert_instagram_profile_pic_url(str(user_data.profile_pic_url))
                
                # Get engagement rate with error handling
                try:
                    engagement_rate = self._calculate_engagement_rate(user_id)
                except Exception as e:
                    self.logger.warning(f"Failed to calculate engagement rate: {str(e)}")
                    engagement_rate = 0
                
                metrics = {
                    "username": username,
                    "followers_count": user_data.follower_count,
                    "following_count": user_data.following_count,
                    "media_count": user_data.media_count,
                    "is_private": user_data.is_private,
                    "is_verified": user_data.is_verified,
                    "engagement_rate": engagement_rate,
                    "profile_picture_url": clean_profile_pic_url,
                }
                return metrics
            except Exception as retry_error:
                self.logger.error(f"Retry failed: {str(retry_error)}")
                # Return placeholder data instead of raising an exception
                return {
                    "username": username,
                    "error": f"Failed to retrieve user data: {str(retry_error)}",
                    "followers_count": 0,
                    "following_count": 0,
                    "media_count": 0,
                    "is_private": False,
                    "is_verified": False,
                    "engagement_rate": 0,
                    "profile_picture_url": "",
                }
        except Exception as e:
            self.logger.error(f"Failed to get user info: {str(e)}")
            # Return placeholder data instead of raising an exception
            return {
                "username": username,
                "error": f"Failed to retrieve user data: {str(e)}",
                "followers_count": 0,
                "following_count": 0,
                "media_count": 0,
                "is_private": False,
                "is_verified": False,
                "engagement_rate": 0,
                "profile_picture_url": "",
            }

    def get_user_followers(self, user_id: str):
        """Get user followers"""
        try:
            return self.client.user_followers(user_id)
        except ClientError as e:
            self.logger.error(f"Failed to get followers: {str(e)}")
            raise

    def get_user_following(self, user_id: str):
        """Get users that a user is following"""
        try:
            return self.client.user_following(user_id)
        except ClientError as e:
            self.logger.error(f"Failed to get following: {str(e)}")
            raise

    def get_user_medias(self, user_id: str, amount: int = 10) -> List[Media]:
        """Get user's media posts"""
        try:
            return self.client.user_medias(user_id, amount)
        except ClientError as e:
            self.logger.error(f"Failed to get user medias: {str(e)}")
            raise

    def _calculate_engagement_rate(self, user_id: str) -> float:
        """Calculate engagement rate for a user"""
        try:
            medias = self.get_user_medias(user_id)
            # Calculate average likes and comments
            likes = [media.like_count for media in medias]
            comments = [media.comment_count for media in medias]
            avg_likes = statistics.mean(likes) if likes else 0
            avg_comments = statistics.mean(comments) if comments else 0
            followers = self.client.user_info(user_id).follower_count
            
            # Prevent division by zero
            if followers == 0:
                return 0
                
            # Simple engagement rate calculation
            engagement_rate = ((avg_likes + avg_comments) / followers) * 100
            return round(engagement_rate, 2)   
        except Exception as e:
            self.logger.error(f"Engagement rate calculation failed for user_id {user_id}: {str(e)}")
            return 0


if __name__ == "__main__":
    instagram_tools = InstagramTools()
    user_info = instagram_tools.user_info_by_username("gorgeousaimodel8")
    print(user_info)
    print(user_info.is_private)

    # user_id = instagram_tools.user_id_by_username("gorgeousaimodel8")
    # print(user_id)
    # user_media_info = instagram_tools.get_user_medias(user_id, amount=5)
    # print(type(user_media_info))
    # print(user_media_info)
    # print(user_media_info[0].like_count)
#
