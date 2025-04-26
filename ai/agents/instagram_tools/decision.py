"""
Decision Layer for Instagram Agent

This module decides what to do next based on current input and memory.
It contains the reasoning logic for the agent.
"""

import logging
import re
import json
from typing import Dict, Any, List, Tuple, Optional, cast

from ..instagram_tools_models.instagram_card_profile_schema import InstagramCardProfileSchema
from .models import (
    PerceptionResponse,
    ThinkingResponse,
    FunctionCallResponse,
    VerificationResponse,
    FinalAnswerResponse,
    MixedResponse,
    ErrorResponse,
    UnknownResponse,
    DecisionOutput,
    ThinkingActionParams,
    FunctionCallActionParams,
    VerificationActionParams,
    FinalAnswerActionParams
)

# Configure logging
logger = logging.getLogger("insta-decision")

def verify_json_output(content: str) -> bool:
    """
    Verify that the JSON output is valid and matches the expected schema
    
    Args:
        content: The content to verify
        
    Returns:
        True if valid, False otherwise
    """
    match = re.search(r"FINAL_ANSWER: (\[.*\])", content, re.DOTALL)

    if match:
        json_string = match.group(1)
        
        try:
            instagram_users = json.loads(json_string)
            
            # Take first element and check if it satisfies the pydantic model
            try:
                profile = InstagramCardProfileSchema.model_validate(instagram_users[0])
                logger.info("Validation successful using model_validate!")
                return True
            except Exception as e:
                logger.error(f"Validation error: {e}")
                return False
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON")
            return False
    else:
        logger.warning("No JSON found in content")
        return False

def determine_next_action(perception_response: PerceptionResponse, memory: Any, usernames: List[str]) -> DecisionOutput:
    """
    Determine the next action based on the perception response and memory
    
    Args:
        perception_response: Response from the perception layer
        memory: Agent's memory
        usernames: List of usernames to process
        
    Returns:
        Decision output with action type and parameters
    """
    # Handle different response types
    if perception_response.type == "function_call":
        function_name = perception_response.function
        params = perception_response.params
        
        # Check if the function call is appropriate based on current state
        if function_name == "get_user_metrics":
            # Extract username from params
            username = params if isinstance(params, str) else params.get("username", "")
            
            # Check if we already have metrics for this user - direct memory access
            if username in memory.processed_usernames:
                logger.warning(f"LLM tried to get metrics for {username} again")
                
                # Get the user metrics
                user_metrics = memory.get_user_metrics(username)
                
                # If the user doesn't have a score yet, redirect to calculate_user_score
                if username not in memory.scored_users and user_metrics:
                    logger.info(f"Redirecting to calculate_user_score for {username}")
                    return DecisionOutput(
                        action_type="function_call",
                        action_params=FunctionCallActionParams(
                            function="calculate_user_score",
                            params=user_metrics
                        )
                    )
                else:
                    logger.info(f"User {username} already has metrics and score, skipping")
                    return DecisionOutput(
                        action_type="thinking",
                        action_params=ThinkingActionParams(
                            content=f"User {username} already has metrics and score. Let's move on to the next step."
                        )
                    )
        
        # Continue with normal function call
        return DecisionOutput(
            action_type="function_call",
            action_params=FunctionCallActionParams(
                function=function_name,
                params=params
            )
        )
    
    elif perception_response.type == "thinking":
        return DecisionOutput(
            action_type="thinking",
            action_params=ThinkingActionParams(
                content=perception_response.content
            )
        )
        
    elif perception_response.type == "verification":
        # Check if verification is successful
        verification_success = verify_json_output(perception_response.content)
        
        return DecisionOutput(
            action_type="verification_success" if verification_success else "verification_failed",
            action_params=VerificationActionParams(
                content=perception_response.content,
                success=verification_success
            )
        )
        
    elif perception_response.type == "final_answer":
        # Try to extract JSON from the content
        try:
            # Handle potential backticks in the content
            content = perception_response.content
            if content.startswith('`') and content.endswith('`'):
                content = content[1:-1]
            
            ranked_users = json.loads(content)
            return DecisionOutput(
                action_type="final_answer",
                action_params=FinalAnswerActionParams(
                    content=perception_response.content,
                    ranked_users=ranked_users
                )
            )
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON in final answer")
            return DecisionOutput(
                action_type="verification_failed",
                action_params=VerificationActionParams(
                    content=perception_response.content,
                    success=False
                )
            )
            
    elif perception_response.type == "mixed":
        # Handle mixed response (thinking + function call)
        return DecisionOutput(
            action_type="mixed",
            action_params=FunctionCallActionParams(
                function=perception_response.function_call.split("|")[0].strip(),
                params=perception_response.function_call.split("|")[1].strip() if "|" in perception_response.function_call else "",
                thinking=perception_response.thinking
            )
        )
        
    else:
        # Handle unknown response type
        logger.warning(f"Unknown response type: {perception_response.type}")
        return DecisionOutput(
            action_type="thinking",
            action_params=ThinkingActionParams(
                content=f"I received an unknown response type: {perception_response.type}. Let me try again."
            )
        )