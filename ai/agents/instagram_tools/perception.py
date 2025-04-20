"""
Perception Layer for Instagram Agent

This module is responsible for translating raw input into structured information
that the agent can reason with. It handles the interaction with the LLM.
"""

import os
import logging
import json
from google import genai
from typing import Dict, Any, List, Union

from ai.models.google_gemini import GoogleGeminiModel
from ai.config import AI_CONFIG

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

def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse the LLM response into a structured format
    
    Args:
        response_text: Raw text response from the LLM
        
    Returns:
        Dictionary with response type and content
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
            return {
                "type": "mixed",
                "thinking": thinking_content,
                "function_call": function_call_line.replace("FUNCTION_CALL:", "").strip()
            }
            
        # Update response_text to only contain the function call
        response_text = function_call_line
    
    # Handle different response formats
    if response_text.startswith("THINKING:"):
        return {
            "type": "thinking",
            "content": response_text.replace("THINKING:", "").strip()
        }
    elif response_text.startswith("FUNCTION_CALL:"):
        function_info = response_text.replace("FUNCTION_CALL:", "").strip()
        func_parts = [x.strip() for x in function_info.split("|", 1)]
        return {
            "type": "function_call",
            "function": func_parts[0],
            "params": func_parts[1] if len(func_parts) > 1 else ""
        }
    elif response_text.startswith("VERIFICATION:"):
        return {
            "type": "verification",
            "content": response_text.replace("VERIFICATION:", "").strip()
        }
    elif response_text.startswith("FINAL_ANSWER:"):
        return {
            "type": "final_answer",
            "content": response_text.replace("FINAL_ANSWER:", "").strip()
        }
    else:
        return {
            "type": "unknown",
            "content": response_text
        }

def process_input(system_prompt: str, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Process input through the LLM to get structured information
    
    Args:
        system_prompt: The system prompt for the LLM
        query: The user query or current state
        context: Additional context like memory or previous responses
        
    Returns:
        Structured response from the LLM
    """
    model = get_gemini_model()
    
    # Construct the full prompt with context
    full_prompt = f"{system_prompt}\n\nQuery: {query}"
    
    # Add context if provided
    if context:
        if "iteration_responses" in context:
            full_prompt += "\n\n" + " ".join(context["iteration_responses"])
        
        if "users_metrics_list" in context:
            full_prompt += f"\nCurrent users_metrics_list: {json.dumps(context['users_metrics_list'])}"
    
    # Get model's response
    try:
        response = model.client.models.generate_content(
            model=AI_CONFIG["google"]["model_name"], 
            contents=full_prompt
        )
        
        # Parse the response
        parsed_response = parse_llm_response(response.text.strip())
        logger.info(f"Processed input, response type: {parsed_response['type']}")
        
        return parsed_response
    except Exception as e:
        logger.error(f"Error processing input: {str(e)}")
        return {
            "type": "error",
            "content": str(e)
        }