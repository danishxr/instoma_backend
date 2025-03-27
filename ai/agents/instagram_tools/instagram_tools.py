import os
import sys
import logging
import statistics
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from instagrapi import Client
from instagrapi.types import Media, User
from typing import List
from instagrapi.exceptions import LoginRequired, ClientError, ClientLoginRequired

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
            if self.client and self._validate_session():
                return self

            self.client = Client()
            session_file = f"{self.username}_session.json"

            if os.path.exists(session_file):
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password)
            else:
                self.client.login(self.username, self.password)
                self.client.dump_settings(session_file)

            return self

        except Exception as e:
            self.logger.error(f"Configuration failed: {str(e)}")
            raise

    def _validate_session(self) -> bool:
        """Validate current session"""
        try:
            self.client.get_timeline_feed()
            return True
        except (LoginRequired, ClientLoginRequired):
            return False

    def user_id_by_username(self, username: str) -> str:
        """Get user ID by username"""
        try:
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

    def user_info_by_username(self, username: str) -> User:
        """Get user information by username"""
        try:
            user_data = self.client.user_info_by_username(username)
            user_id = self.user_id_by_username(username)
            metrics = {
                "username": username,
                "followers_count": user_data.follower_count,
                "following_count": user_data.following_count,
                "media_count": user_data.media_count,
                "is_private": user_data.is_private,
                "is_verified": user_data.is_verified,
                "engagement_rate": self._calculate_engagement_rate(user_id),
            }
            return metrics
        except ClientError as e:
            self.logger.error(f"Failed to get user info: {str(e)}")
            raise
        except UserNotFound:
            self.logger.error(f"User '{username}' not found")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise

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
            # Simple engagement rate calculation
            engagement_rate = ((avg_likes + avg_comments) / followers) * 100
            return round(engagement_rate, 2)   
        except Exception as e:
            print(f"Engagement rate calculation failed for {username}: {e}")
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
