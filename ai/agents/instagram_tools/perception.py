"""
Perception Layer for Instagram Agent

This module is responsible for translating raw input into structured information
that the agent can reason with. It handles the interaction with the LLM.
"""

import os
import logging
import json
from google import genai
from typing import Dict, Any, List, Union, cast

from ai.models.google_gemini import GoogleGeminiModel
from ai.config import AI_CONFIG
from .models import (
    PerceptionInput, 
    PerceptionResponse,
    ThinkingResponse,
    FunctionCallResponse,
    VerificationResponse,
    FinalAnswerResponse,
    MixedResponse,
    ErrorResponse,
    UnknownResponse
)

# Configure logging
logger = logging.getLogger("insta-perception")

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

def parse_llm_response(response_text: str) -> PerceptionResponse:
    """
    Parse the LLM response into a structured format
    
    Args:
        response_text: Raw text response from the LLM
        
    Returns:
        Pydantic model representing the response type
    """
    response_text = response_text.strip()
    
    # Handle mixed format responses
    if "FUNCTION_CALL:" in response_text and not response_text.startswith("FUNCTION_CALL:"):
        # Extract the FUNCTION_CALL part
        function_call_part = response_text[response_text.find("FUNCTION_CALL:"):]
        function_call_line = function_call_part.split("\n")[0].strip()
        
        # Process the thinking part if it exists
        if response_text.startswith("THINKING:"):
            thinking_content = response_text[:response_text.find("FUNCTION_CALL:")].replace("THINKING:", "").strip()
            return MixedResponse(
                thinking=thinking_content,
                function_call=function_call_line.replace("FUNCTION_CALL:", "").strip()
            )
            
        # Update response_text to only contain the function call
        response_text = function_call_line
    
    # Handle different response formats
    if response_text.startswith("THINKING:"):
        return ThinkingResponse(
            content=response_text.replace("THINKING:", "").strip()
        )
    elif response_text.startswith("FUNCTION_CALL:"):
        function_info = response_text.replace("FUNCTION_CALL:", "").strip()
        func_parts = [x.strip() for x in function_info.split("|", 1)]
        return FunctionCallResponse(
            function=func_parts[0],
            params=func_parts[1] if len(func_parts) > 1 else ""
        )
    elif response_text.startswith("VERIFICATION:"):
        return VerificationResponse(
            content=response_text.replace("VERIFICATION:", "").strip()
        )
    elif response_text.startswith("FINAL_ANSWER:"):
        return FinalAnswerResponse(
            content=response_text.replace("FINAL_ANSWER:", "").strip()
        )
    else:
        return UnknownResponse(
            content=response_text
        )

def process_input(system_prompt: str, query: str, context: Dict[str, Any] = None) -> PerceptionResponse:
    """
    Process input through the LLM to get structured information
    
    Args:
        system_prompt: The system prompt for the LLM
        query: The user query or current state
        context: Additional context like memory or previous responses
        
    Returns:
        Structured response from the LLM as a Pydantic model
    """
    model = get_gemini_model()
    
    # Create input model
    perception_input = PerceptionInput(
        system_prompt=system_prompt,
        query=query,
        context=context
    )
    
    # Construct the full prompt with context
    full_prompt = f"{perception_input.system_prompt}\n\nQuery: {perception_input.query}"
    
    # Add context if provided
    if perception_input.context:
        # Add a clear summary of current state to help the LLM understand what's already been done
        if "processed_usernames" in perception_input.context and "scored_users" in perception_input.context:
            processed = perception_input.context["processed_usernames"]
            scored = perception_input.context["scored_users"]
            
            # Create a clear status summary
            status_summary = "\n\nCURRENT STATUS:"
            
            if processed:
                status_summary += f"\n- Users with metrics already retrieved: {', '.join(processed)}"
                if len(processed) == len(perception_input.context.get("users_metrics_list", [])):
                    status_summary += f"\n- All metrics have been successfully retrieved."
            else:
                status_summary += "\n- No user metrics have been retrieved yet."
                
            if scored:
                status_summary += f"\n- Users with scores already calculated: {', '.join(scored)}"
                if len(scored) == len(processed):
                    status_summary += f"\n- All scores have been successfully calculated."
            else:
                status_summary += "\n- No user scores have been calculated yet."
                
            # Add users that need scoring next
            need_scoring = [u for u in processed if u not in scored]
            if need_scoring:
                status_summary += f"\n- Users that need scoring next: {', '.join(need_scoring)}"
            
            # Add ranking status
            if "users_metrics_list" in perception_input.context and perception_input.context["users_metrics_list"]:
                all_have_scores = all("score" in user for user in perception_input.context["users_metrics_list"])
                if all_have_scores and len(processed) == len(perception_input.context["users_metrics_list"]):
                    is_sorted = all(perception_input.context["users_metrics_list"][i].get("score", 0) >= 
                                   perception_input.context["users_metrics_list"][i+1].get("score", 0) 
                                   for i in range(len(perception_input.context["users_metrics_list"])-1))
                    if is_sorted:
                        status_summary += f"\n- User ranking has been completed."
                    else:
                        status_summary += f"\n- All users have scores but ranking needs to be performed."
                
            full_prompt += status_summary
        
        # Add previous iteration responses for context
        if "iteration_responses" in perception_input.context:
            full_prompt += "\n\nPREVIOUS ACTIONS:\n" + "\n".join(perception_input.context["iteration_responses"])
        
        # Add current metrics data
        if "users_metrics_list" in perception_input.context and perception_input.context["users_metrics_list"]:
            metrics_summary = "\n\nCURRENT USER METRICS:"
            for user_metrics in perception_input.context["users_metrics_list"]:
                username = user_metrics.get("username", "unknown")
                has_score = "score" in user_metrics
                metrics_summary += f"\n- {username}: {'Has metrics and score' if has_score else 'Has metrics but needs scoring'}"
            
            full_prompt += metrics_summary
    
    # Get model's response
    try:
        response = model.client.models.generate_content(
            model=AI_CONFIG["google"]["model_name"], 
            contents=full_prompt
        )
        
        # Parse the response
        parsed_response = parse_llm_response(response.text.strip())
        logger.info(f"Processed input, response type: {parsed_response.type}")
        
        return parsed_response
    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        return ErrorResponse(
            content=str(e)
        )