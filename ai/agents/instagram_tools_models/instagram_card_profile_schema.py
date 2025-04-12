from pydantic import BaseModel, Field

class InstagramCardProfileSchema(BaseModel):
    username: str = Field(..., description="The username of the Instagram profile")
    followers_count: int = Field(..., description="The number of followers the profile has")
    following_count: int = Field(..., description="The number of profiles the profile is following")
    media_count: int = Field(..., description="The number of media posts the profile has")
    is_private: bool = Field(..., description="Whether the profile is private or not")
    is_verified: bool = Field(..., description="Whether the profile is verified or not")
    engagement_rate: float = Field(..., description="The engagement rate of the profile")
    profile_picture_url: str = Field(..., description="The URL of the profile picture") 






