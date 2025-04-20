"""
Instagram Agent - Main Module

This module orchestrates the Instagram analysis agent using a layered architecture:
- Perception: Processes input through LLM
- Memory: Stores and manages agent state
- Decision: Determines next actions
- Action: Executes functions and produces outputs
"""

import os
import sys
import json
import logging
from typing import List, Dict, Any

# Fix import path - make it more robust for imports from different locations
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../../../"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Import the layered modules
from ai.agents.instagram_tools.perception import process_input
from ai.agents.instagram_tools.memory import AgentMemory
from ai.agents.instagram_tools.decision import determine_next_action, evaluate_progress
from ai.agents.instagram_tools.action import execute_function, format_iteration_response, format_final_results

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("insta-agent")

# System prompt for the Instagram analysis agent
SYSTEM_PROMPT = """You are an Instagram analysis agent tasked with analyzing and ranking Instagram users based on their metrics.

REASONING PROCESS:
1. First, think step-by-step about what information you need to gather for each user
2. For each username, retrieve their metrics using the appropriate function
3. Once you have metrics, calculate a score for each user
4. Finally, rank all users based on their scores
5. Before providing a final answer, verify that all users have been analyzed and scored

RESPONSE FORMAT:
Respond with EXACTLY ONE of these formats, you cannot use any other format for response:
1. THINKING: <your step-by-step reasoning about what to do next>
2. FUNCTION_CALL: function_name|input
3. VERIFICATION: <verification of results or error checking>
4. FINAL_ANSWER: [ranked_users_json]

AVAILABLE FUNCTIONS:
1. get_user_metrics(username) - Gets metrics for an Instagram user
   - Input: Instagram username as string
   - Output: User metrics including followers, engagement rate, etc.
   - Use when: You need to gather data about a specific Instagram user

2. calculate_user_score(metrics_json) - Calculates a score for a user based on metrics
   - Input: User metrics JSON object
   - Output: Same metrics with an added "score" field
   - Use when: You have user metrics and need to calculate their overall score

3. rank_users(users_list_json) - Ranks users based on their scores
   - Input: List of user metrics with scores
   - Output: Same list sorted by score (highest first)
   - Use when: You have scored all users and need to rank them

ERROR HANDLING:
- If a function returns an error, analyze the error message and decide whether to:
  a) Retry with different parameters
  b) Skip the problematic user and continue with others
  c) Return a partial result with an explanation
- Always check if the returned data makes sense before proceeding

WORKFLOW GUIDELINES:
1. Start by retrieving metrics for each user one by one
2. After getting metrics for a user, calculate their score
3. Once all users have metrics and scores, rank them
4. Verify the results before providing the final answer
5. If any step fails, explain the issue and suggest a workaround

Remember to give ONE response at a time and wait for the result before proceeding to the next step.
"""

def analyze_instagram_users(usernames: List[str], max_iterations: int = 10, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Analyze Instagram users using an agentic workflow with layered architecture.
    
    Args:
        usernames: List of Instagram usernames to analyze
        max_iterations: Maximum number of iterations for the agent
        verbose: Whether to print detailed logs
        
    Returns:
        List of ranked users with their metrics
    """
    # Initialize memory
    memory = AgentMemory()
    
    # Initial query
    query = f"""Analyze these Instagram users and rank them based on their metrics: {usernames}"""
    current_query = query
    
    # Main agent loop
    for iteration in range(max_iterations):
        logger.info(f"---------------------------- Iteration {iteration + 1} ----------------------------")
        if verbose:
            print(f"\n---------------------------- Iteration {iteration + 1} ----------------------------")
        
        # PERCEPTION: Process input through LLM
        context = memory.get_context_dict()
        # TODO: check what does this do wether it takes the prompt and converts it to what.
        parsed_response = process_input(SYSTEM_PROMPT, current_query, context)
        
        if verbose:
            print(f"LLM Response: {parsed_response}")
        
        # DECISION: Determine next action
        action_type, action_params = determine_next_action(parsed_response, memory, usernames)
        
        # ACTION: Execute the determined action
        if action_type == "function_call":
            function_name = action_params.get("function")
            params = action_params.get("params")
            
            # Execute the function
            result = execute_function(function_name, params)
            action_params["result"] = result
            
            # Update memory based on function result
            if function_name == "get_user_metrics":
                memory.store_user_metrics(result)
            elif function_name == "calculate_user_score":
                if "username" in result:
                    memory.store_user_score(result["username"], result.get("score", 0))
            elif function_name == "rank_users":
                memory.update_users_list(result)
        
        elif action_type == "mixed":
            function_name = action_params.get("function")
            params = action_params.get("params")
            
            # Execute the function
            result = execute_function(function_name, params)
            action_params["result"] = result
            
            # Update memory based on function result
            if function_name == "get_user_metrics":
                memory.store_user_metrics(result)
            elif function_name == "calculate_user_score":
                if "username" in result:
                    memory.store_user_score(result["username"], result.get("score", 0))
            elif function_name == "rank_users":
                memory.update_users_list(result)
        
        elif action_type == "final_answer":
            ranked_users = action_params.get("ranked_users", [])
            format_final_results(ranked_users, verbose)
            return ranked_users
        
        # Format and store the iteration response
        response_text = format_iteration_response(iteration + 1, action_type, action_params)
        memory.add_iteration_response(response_text)
        
        # Update the query for the next iteration
        if iteration > 0:
            current_query = f"{query}\n\nWhat should I do next?"
        
        # Print result if verbose and we have a result
        if verbose and "result" in action_params:
            print(f"  Result: {action_params['result']}")
    
    # If we reach max iterations without a final answer, return the current list
    logger.warning(f"Reached maximum iterations ({max_iterations}) without final answer")
    return memory.get_all_users_metrics()

# Main execution
if __name__ == "__main__":
    # List of users to analyze
    list_of_users = ["sunnyleone", "beingsalmankhan"]

    # Run the analysis
    ranked_users = analyze_instagram_users(list_of_users, verbose=True)

    # Print results
    print("\n# Final Instagram User Ranking Results")
    for i, user in enumerate(ranked_users, 1):
        print(f"\n## {i}. {user['username']} (Score: {user.get('score', 'N/A')})")
        print(f"- Followers: {user.get('followers_count', 'N/A')}")
        print(f"- Engagement Rate: {user.get('engagement_rate', 'N/A')}%")
        print(f"- Media Count: {user.get('media_count', 'N/A')}")
