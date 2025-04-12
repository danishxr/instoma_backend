# Update the import section to ensure proper imports when called from router
import os
import sys
import json
import re
import logging
from typing import List, Dict, Any
import statistics
from google import genai
from pydantic import BaseModel
from ..instagram_tools_models.instagram_card_profile_schema import InstagramCardProfileSchema
# Fix import path - make it more robust for imports from different locations
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "../../../"))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from ai.agents.instagram_tools.instagram_tools import InstagramTools
from ai.models.google_gemini import GoogleGeminiModel
from ai.config import AI_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("insta-agent")

# Instagram tools instance
insta_tools = InstagramTools()

def get_gemini_model():
    """Initialize and return the Gemini model"""
    if "google" not in AI_CONFIG:
        AI_CONFIG["google"] = {
            "api_key": os.getenv("GOOGLE_API_KEY"),
            "model_name": "gemini-2.0-flash"
        }

    # Initialize and configure model
    model = GoogleGeminiModel()
    return model.configure(AI_CONFIG)


# Function to verify the JSON output
def verify_the_json_output(content: str) -> bool:
    """The function checks the LLM metrics data and vaildates pydantic model"""
    match = re.search(r"FINAL_ANSWER: (\[.*\])", content, re.DOTALL)

    if match:
        json_string = match.group(1)

        instagram_users = json.loads(json_string)

        # Take first element and check if it statisfies the pydantic model

        try:
            profile = InstagramCardProfileSchema.model_validate(instagram_users[0])

            print("Validation successful using model_validate!")

            return True

        except ValidationError as e:

            print(f"Validation error: {e}")

            return True
    else:

        return False


# Function caller to execute the selected tool
def function_caller(func_name, params):
    """Execute the function based on name and parameters"""
    if func_name == "get_user_metrics":
        return insta_tools.user_info_by_username(params)
    elif func_name == "calculate_user_score":
        return calculate_user_score(json.loads(params))
    elif func_name == "rank_users":
        return rank_users(json.loads(params))
    else:
        return f"Error: Unknown function {func_name}"

def calculate_user_score(metrics):
    """Calculate a score for a user based on their metrics"""
    if "error" in metrics:
        return 0
        
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

def rank_users(users_list):
    """Rank users based on their scores"""
    sorted_users = sorted(users_list, key=lambda x: x.get("score", 0), reverse=True)
    return sorted_users

def analyze_instagram_users(usernames: List[str], max_iterations: int = 10, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Analyze Instagram users using an agentic workflow.
    
    Args:
        usernames: List of Instagram usernames to analyze
        max_iterations: Maximum number of iterations for the agent
        verbose: Whether to print detailed logs
        
    Returns:
        List of ranked users with their metrics
    """
    gemini_model = get_gemini_model()
    last_response = None
    iteration = 0
    iteration_response = []
    users_metrics_list = []

    system_prompt = """You are an Instagram analysis agent tasked with analyzing and ranking Instagram users based on their metrics.

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

    query = f"""Analyze these Instagram users and rank them based on their metrics: {usernames}"""

    while iteration < max_iterations:
        logger.info(
            f"---------------------------- Iteration {iteration + 1} ----------------------------"
        )
        if verbose:
            print(f"\n---------------------------- Iteration {iteration + 1} ----------------------------")

        if last_response is None:
            current_query = query
        else:
            current_query = current_query + "\n\n" + " ".join(iteration_response)
            current_query = current_query + "\nWhat should I do next?"

        # Get model's response
        prompt = f"{system_prompt}\n\nQuery: {current_query}\nCurrent users_metrics_list: {json.dumps(users_metrics_list)}"
        response = gemini_model.client.models.generate_content(
            model=AI_CONFIG["google"]["model_name"], contents=prompt
        )

        response_text = response.text.strip()
        if verbose:
            print(f"LLM Response: {response_text}")

        # Check if there's an embedded FUNCTION_CALL within the response
        if "FUNCTION_CALL:" in response_text and not response_text.startswith("FUNCTION_CALL:"):
            # Extract the FUNCTION_CALL part
            function_call_part = response_text[response_text.find("FUNCTION_CALL:"):]
            function_call_line = function_call_part.split("\n")[0].strip()

            # Log the mixed format issue
            logger.warning(f"Mixed response format detected. Extracting function call: {function_call_line}")
            if verbose:
                print(f"Mixed response format detected. Extracting function call: {function_call_line}")

            # Process the thinking part if it exists
            if response_text.startswith("THINKING:"):
                thinking_content = response_text[:response_text.find("FUNCTION_CALL:")].replace("THINKING:", "").strip()
                logger.info(f"Agent thinking: {thinking_content}")
                if verbose:
                    print(f"Agent thinking: {thinking_content}")

                # Add thinking to iteration response
                iteration_response.append(f"You thought: {thinking_content}")

            # Update response_text to only contain the function call
            response_text = function_call_line

        # Handle THINKING response format
        if response_text.startswith("THINKING:"):
            thinking_content = response_text.replace("THINKING:", "").strip()
            logger.info(f"Agent thinking: {thinking_content}")
            if verbose:
                print(f"Agent thinking: {thinking_content}")

            # Add thinking to iteration response
            iteration_response.append(f"You thought: {thinking_content}")
            last_response = "thinking"
            iteration += 1
            continue

        # Handle VERIFICATION response format
        elif response_text.startswith("VERIFICATION:"):
            verification_content = response_text.replace("VERIFICATION:", "").strip()
            logger.info(f"Agent verification: {verification_content}")
            # Add verification to iteration response
            verification_result = verify_the_json_output(verification_content)

            if verification_result:
                logger.info(f"Verification successful: {verification_content}")
                if verbose:
                    print(f"Verification successful: {verification_content}")
                iteration_response.append(f"You verified: {verification_content} + proceed with FINAL ANSWER" )
                last_response = "verification"
            else:
                logger.error(f"Verification failed: {verification_content}")
                if verbose:
                    print(f"Verification failed: {verification_content}")

            iteration += 1
            continue

        # Handle FUNCTION_CALL response format
        elif response_text.startswith("FUNCTION_CALL:"):
            _, function_info = response_text.split(":", 1)
            func_name, params = [x.strip() for x in function_info.split("|", 1)]

            logger.info(f"Calling function: {func_name} with params: {params}")
            iteration_result = function_caller(func_name, params)

            # If we're getting user metrics, add to our list
            if func_name == "get_user_metrics":
                users_metrics_list.append(iteration_result)
            # If we're calculating a score, update the corresponding user in the list
            elif func_name == "calculate_user_score":
                for i, user in enumerate(users_metrics_list):
                    if user["username"] == iteration_result["username"]:
                        users_metrics_list[i] = iteration_result
            # If we're ranking, update the entire list
            elif func_name == "rank_users":
                users_metrics_list = iteration_result

            last_response = iteration_result
            iteration_response.append(f"In iteration {iteration + 1} you called {func_name} with {params} parameters, and the function returned {json.dumps(iteration_result)}.")

        # Handle FINAL_ANSWER response format
        elif response_text.startswith("FINAL_ANSWER:"):
            if verbose:
                print("\n=== Agent Execution Complete ===")
            # Extract the final ranked list
            final_result = response_text.replace("FINAL_ANSWER:", "").strip()
            try:
                ranked_users = json.loads(final_result)
                if verbose:
                    print("\n# Instagram User Ranking Results")
                    for i, user in enumerate(ranked_users, 1):
                        print(f"\n## {i}. {user['username']} (Score: {user.get('score', 'N/A')})")
                        print(f"- Followers: {user.get('followers_count', 'N/A')}")
                        print(f"- Engagement Rate: {user.get('engagement_rate', 'N/A')}%")
                        print(f"- Media Count: {user.get('media_count', 'N/A')}")
                return ranked_users
            except json.JSONDecodeError:
                logger.error("Could not parse final result as JSON")
                if verbose:
                    print("Could not parse final result as JSON")
                # If we can't parse the final answer, return the current list
                return users_metrics_list
            break
        else:
            # Handle unexpected response format
            logger.warning(f"Unexpected response format: {response_text}")
            if verbose:
                print(f"Unexpected response format: {response_text}")

            # TODO To restric adding a response to the iteration_response list, we can remove the following line:
            # iteration_response.append(f"You provided an unexpected response format. Please use one of the specified formats.")

        if verbose and 'iteration_result' in locals():
            print(f"  Result: {iteration_result}")

        iteration += 1

    # If we reach max iterations without a final answer, return the current list
    logger.warning(f"Reached maximum iterations ({max_iterations}) without final answer")
    return users_metrics_list

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
