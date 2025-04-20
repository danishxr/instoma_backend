"""
Action Layer for Instagram Agent

This module executes the decisions made by the decision layer.
It handles function calls, API interactions, and produces outputs.
"""

import logging
import json
from typing import Dict, Any, List, Callable, Optional

from .instagram_tools import InstagramTools

# Configure logging
logger = logging.getLogger("insta-action")

# Instagram tools instance
insta_tools = InstagramTools()

def calculate_user_score(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate a score for a user based on their metrics
    
    Args:
        metrics: User metrics dictionary
        
    Returns:
        Updated metrics with score
    """
    if "error" in metrics:
        return metrics
        
    # Scoring factors (adjust weights as needed)
    followers_weight = 0.4
    engagement_weight = 0.5
    media_count_weight = 0.1
    
    # Calculate normalized scores (0-100 scale)
    followers_score = min(100, metrics["followers_count"] / 1000 * 10)
    engagement_score = min(100, metrics["engagement_rate"] * 10)
    media_score = min(100, metrics["media_count"] / 10 * 10)
    
    # Calculate weighted score
    total_score = (
        followers_score * followers_weight +
        engagement_score * engagement_weight +
        media_score * media_count_weight
    )
    
    metrics["score"] = round(total_score, 2)
    return metrics

def rank_users(users_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank users based on their scores
    
    Args:
        users_list: List of user metrics with scores
        
    Returns:
        Sorted list of users by score (highest first)
    """
    sorted_users = sorted(users_list, key=lambda x: x.get("score", 0), reverse=True)
    return sorted_users

def execute_function(function_name: str, params: Any) -> Dict[str, Any]:
    """
    Execute a function based on name and parameters
    
    Args:
        function_name: Name of the function to execute
        params: Parameters for the function
        
    Returns:
        Result of the function execution
    """
    logger.info(f"Executing function: {function_name} with params: {params}")
    
    try:
        if function_name == "get_user_metrics":
            return insta_tools.user_info_by_username(params)
        elif function_name == "calculate_user_score":
            return calculate_user_score(json.loads(params))
        elif function_name == "rank_users":
            return rank_users(json.loads(params))
        else:
            error_msg = f"Unknown function {function_name}"
            logger.error(error_msg)
            return {"error": error_msg}
    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

def format_iteration_response(
    iteration: int, 
    action_type: str, 
    action_result: Any
) -> str:
    """
    Format the response for an iteration
    
    Args:
        iteration: Current iteration number
        action_type: Type of action performed
        action_result: Result of the action
        
    Returns:
        Formatted response string
    """
    if action_type == "thinking":
        return f"You thought: {action_result.get('content')}"
    
    elif action_type == "function_call":
        function = action_result.get("function")
        params = action_result.get("params")
        result = action_result.get("result", {})
        return f"In iteration {iteration} you called {function} with {params} parameters, and the function returned {json.dumps(result)}."
    
    elif action_type == "verification_success":
        return f"You verified: {action_result.get('content')} + proceed with FINAL ANSWER"
    
    elif action_type == "verification_failed":
        return f"Verification failed: {action_result.get('content')}"
    
    elif action_type == "mixed":
        thinking = action_result.get("thinking")
        function = action_result.get("function")
        params = action_result.get("params")
        result = action_result.get("result", {})
        return f"You thought: {thinking}\nIn iteration {iteration} you called {function} with {params} parameters, and the function returned {json.dumps(result)}."
    
    elif action_type == "error":
        return f"Error occurred: {action_result.get('message')}"
    
    else:
        return f"Unknown action type: {action_type}"

def format_final_results(ranked_users: List[Dict[str, Any]], verbose: bool = False) -> Optional[str]:
    """
    Format the final results for display
    
    Args:
        ranked_users: List of ranked users
        verbose: Whether to print detailed output
        
    Returns:
        Formatted results string if verbose is True, None otherwise
    """
    if not verbose:
        return None
        
    output = "\n=== Agent Execution Complete ===\n"
    output += "\n# Instagram User Ranking Results\n"
    
    for i, user in enumerate(ranked_users, 1):
        output += f"\n## {i}. {user['username']} (Score: {user.get('score', 'N/A')})\n"
        output += f"- Followers: {user.get('followers_count', 'N/A')}\n"
        output += f"- Engagement Rate: {user.get('engagement_rate', 'N/A')}%\n"
        output += f"- Media Count: {user.get('media_count', 'N/A')}\n"
    
    if verbose:
        print(output)
    
    return output