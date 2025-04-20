"""
Decision Layer for Instagram Agent

This module decides what to do next based on current input and memory.
It contains the reasoning logic for the agent.
"""

import logging
import re
import json
from typing import Dict, Any, List, Tuple, Optional

from ..instagram_tools_models.instagram_card_profile_schema import InstagramCardProfileSchema

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

def determine_next_action(
    parsed_response: Dict[str, Any], 
    memory: Any, 
    all_usernames: List[str]
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Determine the next action based on the parsed response and memory
    
    Args:
        parsed_response: The parsed response from the perception layer
        memory: The agent's memory
        all_usernames: List of all usernames to process
        
    Returns:
        Tuple of (action_type, action_params)
    """
    response_type = parsed_response.get("type")
    
    # Handle thinking responses
    if response_type == "thinking":
        logger.info(f"Agent thinking: {parsed_response.get('content')}")
        return "thinking", {"content": parsed_response.get("content")}
    
    # Handle verification responses
    elif response_type == "verification":
        verification_content = parsed_response.get("content")
        verification_result = verify_json_output(verification_content)
        
        if verification_result:
            logger.info(f"Verification successful: {verification_content}")
            return "verification_success", {"content": verification_content}
        else:
            logger.error(f"Verification failed: {verification_content}")
            return "verification_failed", {"content": verification_content}
    
    # Handle function call responses
    elif response_type == "function_call":
        func_name = parsed_response.get("function")
        params = parsed_response.get("params")
        
        logger.info(f"Function call: {func_name} with params: {params}")
        return "function_call", {"function": func_name, "params": params}
    
    # Handle final answer responses
    elif response_type == "final_answer":
        final_result = parsed_response.get("content")
        try:
            ranked_users = json.loads(final_result)
            logger.info(f"Final answer with {len(ranked_users)} ranked users")
            return "final_answer", {"ranked_users": ranked_users}
        except json.JSONDecodeError:
            logger.error("Could not parse final result as JSON")
            return "error", {"message": "Could not parse final result as JSON"}
    
    # Handle mixed format responses
    elif response_type == "mixed":
        thinking = parsed_response.get("thinking")
        function_call = parsed_response.get("function_call")
        
        logger.info(f"Mixed response - thinking: {thinking}")
        logger.info(f"Mixed response - function call: {function_call}")
        
        # Extract function name and params
        func_parts = [x.strip() for x in function_call.split("|", 1)]
        func_name = func_parts[0]
        params = func_parts[1] if len(func_parts) > 1 else ""
        
        return "mixed", {
            "thinking": thinking,
            "function": func_name,
            "params": params
        }
    
    # Handle unknown or error responses
    else:
        logger.warning(f"Unknown response type: {response_type}")
        return "unknown", {"content": parsed_response.get("content")}

def evaluate_progress(memory: Any, all_usernames: List[str]) -> Dict[str, Any]:
    """
    Evaluate the current progress of the agent
    
    Args:
        memory: The agent's memory
        all_usernames: List of all usernames to process
        
    Returns:
        Dictionary with progress information
    """
    users_metrics = memory.get_all_users_metrics()
    unprocessed = memory.get_unprocessed_usernames(all_usernames)
    unscored = memory.get_unscored_users()
    
    all_processed = memory.all_users_processed(all_usernames)
    all_scored = memory.all_users_scored()
    
    return {
        "total_users": len(all_usernames),
        "processed_users": len(users_metrics),
        "unprocessed_users": unprocessed,
        "unscored_users": [u.get("username") for u in unscored],
        "all_processed": all_processed,
        "all_scored": all_scored,
        "ready_for_ranking": all_processed and all_scored
    }