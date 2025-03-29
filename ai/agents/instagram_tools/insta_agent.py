# Update the import section to ensure proper imports when called from router
import os
import sys
import json
import logging
from typing import List, Dict, Any
import statistics
from google import genai

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

    system_prompt = """You are an Instagram analysis agent. Respond with EXACTLY ONE of these formats:
    1. FUNCTION_CALL: function_name|input
    2. FINAL_ANSWER: [ranked_users_json]
    
    where function_name is one of the following:
    1. get_user_metrics(username) - Gets metrics for an Instagram user
    2. calculate_user_score(metrics_json) - Calculates a score for a user based on metrics
    3. rank_users(users_list_json) - Ranks users based on their scores
    
    Your goal is to analyze Instagram users, calculate their scores, and rank them.
    DO NOT include multiple responses. Give ONE response at a time."""

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

        if "FUNCTION_CALL:" in response_text:
            _, function_info = response_text.split(":", 1)
            func_name, params = [x.strip() for x in function_info.split("|", 1)]

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

        # Check if it's the final answer
        elif "FINAL_ANSWER:" in response_text:
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
                if verbose:
                    print("Could not parse final result as JSON")
                # If we can't parse the final answer, return the current list
                return users_metrics_list
            break

        if verbose:
            print(f"  Result: {iteration_result}")

        last_response = iteration_result
        iteration_response.append(f"In iteration {iteration + 1} you called {func_name} with {params} parameters, and the function returned {json.dumps(iteration_result)}.")

        iteration += 1

    # If we reach max iterations without a final answer, return the current list
    return users_metrics_list

# Main execution
if __name__ == "__main__":
    # List of users to analyze
    list_of_users = ["gorgeousaimodel8", "sillytechy"]
    
    # Run the analysis
    ranked_users = analyze_instagram_users(list_of_users, verbose=True)
    
    # Print results
    print("\n# Final Instagram User Ranking Results")
    for i, user in enumerate(ranked_users, 1):
        print(f"\n## {i}. {user['username']} (Score: {user.get('score', 'N/A')})")
        print(f"- Followers: {user.get('followers_count', 'N/A')}")
        print(f"- Engagement Rate: {user.get('engagement_rate', 'N/A')}%")
        print(f"- Media Count: {user.get('media_count', 'N/A')}")
