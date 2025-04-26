"""
Action Layer for Instagram Agent

This module executes the decisions made by the decision layer.
It handles function calls, API interactions, and produces outputs.
"""

import logging
import json
from typing import Dict, Any, List, Callable, Optional, Union

from .instagram_tools import InstagramTools
from .models import UserMetrics, UserMetricsResult, UserScoreResult, RankedUsersResult

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
            # Handle string or dict parameters
            username = params if isinstance(params, str) else params.get("username")
            result = insta_tools.user_info_by_username(username)
            return result
            
        elif function_name == "calculate_user_score":
            # Handle string or dict parameters
            metrics = json.loads(params) if isinstance(params, str) else params
            result = calculate_user_score(metrics)
            return result
            
        elif function_name == "rank_users":
            # Handle string or dict parameters
            users_list = json.loads(params) if isinstance(params, str) else params
            result = rank_users(users_list)
            return result
            
        else:
            logger.error(f"Unknown function: {function_name}")
            return {"error": f"Unknown function: {function_name}"}
            
    except Exception as e:
        logger.error(f"Error executing function {function_name}: {str(e)}")
        return {"error": str(e), "function": function_name}

def format_iteration_response(iteration: int, action_type: str, action_params: Dict[str, Any]) -> str:
    """
    Format the response for an iteration
    
    Args:
        iteration: Iteration number
        action_type: Type of action taken
        action_params: Parameters of the action
        
    Returns:
        Formatted response string
    """
    if action_type == "function_call":
        function_name = action_params.get("function")
        result = action_params.get("result", {})
        
        if "error" in result:
            return f"Iteration {iteration}: Called {function_name} but got error: {result['error']}"
        else:
            return f"Iteration {iteration}: Called {function_name} successfully"
            
    elif action_type == "mixed":
        function_name = action_params.get("function")
        result = action_params.get("result", {})
        
        if "error" in result:
            return f"Iteration {iteration}: Thought about next steps and called {function_name} but got error: {result['error']}"
        else:
            return f"Iteration {iteration}: Thought about next steps and called {function_name} successfully"
            
    elif action_type == "thinking":
        return f"Iteration {iteration}: Thinking about next steps"
        
    elif action_type == "verification_success":
        return f"Iteration {iteration}: Verified results successfully"
        
    elif action_type == "verification_failed":
        return f"Iteration {iteration}: Verification failed"
        
    elif action_type == "final_answer":
        return f"Iteration {iteration}: Provided final answer with ranked users"
        
    else:
        return f"Iteration {iteration}: {action_type}"

def format_final_results(ranked_users: List[Dict[str, Any]], verbose: bool = False) -> None:
    """
    Format and display the final results
    
    Args:
        ranked_users: List of ranked users
        verbose: Whether to print detailed output
    """
    if not verbose:
        return
        
    print("\n# Final Instagram User Ranking Results")
    for i, user in enumerate(ranked_users, 1):
        print(f"\n## {i}. {user['username']} (Score: {user.get('score', 'N/A')})")
        print(f"- Followers: {user.get('followers_count', 'N/A')}")
        print(f"- Engagement Rate: {user.get('engagement_rate', 'N/A')}%")
        print(f"- Media Count: {user.get('media_count', 'N/A')}")