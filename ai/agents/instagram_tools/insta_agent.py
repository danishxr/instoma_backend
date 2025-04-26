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
from ai.agents.instagram_tools.decision import determine_next_action
from ai.agents.instagram_tools.action import execute_function, format_iteration_response, format_final_results
from ai.agents.instagram_tools.models import (
    PerceptionResponse,
    DecisionOutput,
    FunctionCallActionParams,
    FinalAnswerActionParams,
    ThinkingActionParams,
    VerificationActionParams
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("insta-agent")

# System prompt for the Instagram analysis agent
# Update the SYSTEM_PROMPT section that defines the FINAL_ANSWER format:

SYSTEM_PROMPT = """You are an Instagram analysis agent tasked with analyzing and ranking Instagram users based on their metrics.

REASONING PROCESS:
YOU MUST STRICTLY FOLLOW ONE OF THESE FORMATS FOR EACH RESPONSE:
1. THINKING: <your step-by-step reasoning about what to do next> 
2. FUNCTION_CALL: function_name|input 
3. VERIFICATION: <verification of results or error checking> 
4. FINAL_ANSWER: [{"username": "user1", "followers_count": 1000, ...}, {"username": "user2", ...}]

IMPORTANT: For FINAL_ANSWER, provide the JSON array directly without any backticks, markdown formatting, or additional text.

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

def analyze_instagram_users(usernames: List[str], max_iterations: int = 20, verbose: bool = False) -> List[Dict[str, Any]]:
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
    
    # Track if we've already ranked users
    users_ranked = False
    
    # Main agent loop
    for iteration in range(max_iterations):
        logger.info(f"---------------------------- Iteration {iteration + 1} ----------------------------")
        if verbose:
            print(f"\n---------------------------- Iteration {iteration + 1} ----------------------------")
        
        # PERCEPTION: Process input through LLM
        context = memory.get_context_dict()
        parsed_response = process_input(SYSTEM_PROMPT, current_query, context)
        
        if verbose:
            print(f"LLM Response: {parsed_response}")
        
        # DECISION: Determine next action
        decision_output = determine_next_action(parsed_response, memory, usernames)
        action_type = decision_output.action_type
        action_params = decision_output.action_params
        
        # ACTION: Execute the determined action
        if action_type == "function_call" or action_type == "mixed":
            # Cast to the appropriate type for better type checking
            if isinstance(action_params, FunctionCallActionParams):
                function_name = action_params.function
                params = action_params.params
                
                # Check if we should call rank_users
                if function_name == "rank_users":
                    # Skip if ranking is already completed
                    if hasattr(memory, 'ranking_completed') and memory.ranking_completed:
                        logger.info("Skipping redundant rank_users call as ranking is already completed")
                        response_text = f"Iteration {iteration + 1}: Skipped redundant ranking, ranking already completed"
                        memory.add_iteration_response(response_text)
                        current_query = f"{query}\n\nRanking is already complete. Please verify the results and provide a final answer."
                        continue
                    
                    # Skip ranking if not all users are scored yet
                    if not memory.all_users_scored():
                        logger.info("Skipping rank_users call as not all users are scored yet")
                        response_text = f"Iteration {iteration + 1}: Skipped premature ranking, waiting for all users to be scored first"
                        memory.add_iteration_response(response_text)
                        
                        # Update query to guide the agent to score remaining users first
                        unscored_users = memory.get_unscored_users()
                        if unscored_users:
                            unscored_usernames = [u.get("username") for u in unscored_users if "username" in u]
                            current_query = f"{query}\n\nPlease calculate scores for these users first: {unscored_usernames}"
                        continue
                
                # Execute the function
                result = execute_function(function_name, params)
                action_params.result = result
                
                # Update memory based on function result
                if function_name == "get_user_metrics":
                    memory.store_user_metrics(result)
                elif function_name == "calculate_user_score":
                    if "username" in result:
                        memory.store_user_score(result["username"], result.get("score", 0))
                        
                        # Check if all users are scored and suggest ranking if they are
                        if memory.all_users_processed(usernames) and memory.all_users_scored():
                            current_query = f"{query}\n\nAll users have metrics and scores. Please rank the users now."
                elif function_name == "rank_users":
                    memory.update_users_list(result)
                    users_ranked = True
                    
                    # After ranking, force a verification step if all users have been processed and scored
                    if users_ranked and memory.all_users_processed(usernames) and memory.all_users_scored():
                        # Update the query to prompt for verification and final answer
                        current_query = f"{query}\n\nAll users have been ranked. Please verify the results and provide a final answer."
                        
                        # Add a flag to prevent further rank_users calls
                        memory.ranking_completed = True
                        
                        # Log that ranking is complete
                        logger.info("User ranking completed, moving to verification")
                        continue
        
        elif action_type == "verification_success":
            # If verification is successful, move directly to final answer
            if isinstance(action_params, VerificationActionParams) and action_params.success:
                # Get the ranked users from memory
                ranked_users = memory.get_all_users_metrics()
                format_final_results(ranked_users, verbose)
                return ranked_users
        
        elif action_type == "final_answer":
            # Cast to the appropriate type for better type checking
            if isinstance(action_params, FinalAnswerActionParams):
                ranked_users = action_params.ranked_users
                format_final_results(ranked_users, verbose)
                return ranked_users
        
        # Format and store the iteration response
        response_text = format_iteration_response(iteration + 1, action_type, action_params.dict())
        memory.add_iteration_response(response_text)
        
        # Update the query for the next iteration
        if iteration > 0 and not users_ranked:
            current_query = f"{query}\n\nWhat should I do next?"
        elif users_ranked and memory.all_users_processed(usernames) and memory.all_users_scored():
            # If users are ranked and all processing is complete, prompt for verification and final answer
            current_query = f"{query}\n\nAll users have been ranked. Please verify the results and provide a final answer."
        
        # Print result if verbose and we have a result
        if verbose and isinstance(action_params, FunctionCallActionParams) and action_params.result:
            print(f"  Result: {action_params.result}")
    
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
