"""
Pydantic models for Instagram Agent components

This module defines the data models for communication between different layers
of the Instagram agent architecture.
"""

from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field


# Perception Layer Models
class PerceptionInput(BaseModel):
    """Input for the perception layer"""
    system_prompt: str
    query: str
    context: Optional[Dict[str, Any]] = None


class ThinkingResponse(BaseModel):
    """Model for thinking response"""
    type: Literal["thinking"] = "thinking"
    content: str


class FunctionCallResponse(BaseModel):
    """Model for function call response"""
    type: Literal["function_call"] = "function_call"
    function: str
    params: str


class VerificationResponse(BaseModel):
    """Model for verification response"""
    type: Literal["verification"] = "verification"
    content: str


class FinalAnswerResponse(BaseModel):
    """Model for final answer response"""
    type: Literal["final_answer"] = "final_answer"
    content: str


class MixedResponse(BaseModel):
    """Model for mixed response (thinking + function call)"""
    type: Literal["mixed"] = "mixed"
    thinking: str
    function_call: str


class ErrorResponse(BaseModel):
    """Model for error response"""
    type: Literal["error"] = "error"
    content: str


class UnknownResponse(BaseModel):
    """Model for unknown response format"""
    type: Literal["unknown"] = "unknown"
    content: str


# Union type for all possible perception responses
PerceptionResponse = Union[
    ThinkingResponse, 
    FunctionCallResponse, 
    VerificationResponse, 
    FinalAnswerResponse, 
    MixedResponse,
    ErrorResponse,
    UnknownResponse
]


# Decision Layer Models
class ActionParams(BaseModel):
    """Base model for action parameters"""
    pass


class ThinkingActionParams(ActionParams):
    """Parameters for thinking action"""
    content: str


class FunctionCallActionParams(ActionParams):
    """Parameters for function call action"""
    function: str
    params: Any
    result: Optional[Dict[str, Any]] = None


class VerificationActionParams(ActionParams):
    """Parameters for verification action"""
    content: str


class FinalAnswerActionParams(ActionParams):
    """Parameters for final answer action"""
    ranked_users: List[Dict[str, Any]]


class DecisionOutput(BaseModel):
    """Output from the decision layer"""
    action_type: str
    action_params: ActionParams


# Memory Layer Models
class UserMetrics(BaseModel):
    """Model for user metrics"""
    username: str
    followers_count: int
    following_count: int
    media_count: int
    engagement_rate: float
    is_private: bool
    is_verified: bool
    profile_picture_url: Optional[str] = None
    score: Optional[float] = None


class MemoryState(BaseModel):
    """Model for the complete memory state"""
    users_metrics: List[UserMetrics] = Field(default_factory=list)
    iteration_responses: List[str] = Field(default_factory=list)
    processed_usernames: List[str] = Field(default_factory=list)
    scored_users: List[str] = Field(default_factory=list)


class MemoryContext(BaseModel):
    """Model for memory context provided to perception"""
    users_metrics_list: List[Dict[str, Any]] = Field(default_factory=list)
    iteration_responses: List[str] = Field(default_factory=list)
    processed_usernames: List[str] = Field(default_factory=list)
    scored_users: List[str] = Field(default_factory=list)


# Action Layer Models
class FunctionResult(BaseModel):
    """Base model for function execution results"""
    pass


class UserMetricsResult(FunctionResult, UserMetrics):
    """Result of get_user_metrics function"""
    pass


class UserScoreResult(FunctionResult, UserMetrics):
    """Result of calculate_user_score function"""
    pass


class RankedUsersResult(FunctionResult):
    """Result of rank_users function"""
    users: List[UserMetrics]