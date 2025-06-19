# Instagram Automation Plugin (Instoma)

A powerful backend service for automating Instagram content creation and posting with AI-powered caption and hashtag generation.

## Overview

This project provides a FastAPI-based backend service that combines AI vision models with Instagram API integration to automate the process of creating and posting content to Instagram. The system can analyze images, generate engaging captions and relevant hashtags, and post directly to Instagram.

## Features

- **AI-Powered Caption Generation**: Analyze images and generate engaging captions using various AI models
- **Hashtag Recommendation**: Generate relevant hashtags for your content
- **Instagram User Analysis**: Analyze and rank Instagram users based on their metrics
- **Multiple AI Model Support**: 
  - Google Gemini
  - Llama (local)
  - Ollama integration
- **Instagram API Integration**: Post content directly to Instagram
- **Flexible Configuration**: Switch between different AI providers easily
- 

## Architecture

### Instagram Agent Architecture

The Instagram analysis agent uses a layered architecture to analyze and rank Instagram users:

1. **Perception Layer** (`perception.py`): Processes input through LLM
2. **Memory Layer** (`memory.py`): Stores and manages agent state
3. **Decision Layer** (`decision.py`): Determines next actions
4. **Action Layer** (`action.py`): Executes functions and produces outputs

#### Agent Workflow

The Instagram agent follows this workflow:

1. Client calls `analyze_instagram_users()` with usernames, max_iterations, and verbose parameters
2. Agent initializes the Memory component
3. For each iteration:
   - Gets the current context from Memory
   - Processes input through Perception to get LLM response
   - Determines the next action using Decision
   - Based on action type:
     - For function calls: executes the function and updates memory based on function type
     - For final answer: formats results and returns to client
   - Formats the iteration response and adds it to memory
4. If max iterations are reached without a final answer, returns all user metrics from memory

``` mermaid
sequenceDiagram
    participant Client
    participant InstaAgent as insta_agent.py
    participant Perception as perception.py
    participant Memory as memory.py
    participant Decision as decision.py
    participant Action as action.py
    
    Client->>+InstaAgent: 1. analyze_instagram_users(usernames, max_iterations, verbose)
    InstaAgent->>+Memory: 2. Initialize AgentMemory()
    Memory-->>-InstaAgent: memory object
    
    rect rgb(230, 240, 255)
        Note over InstaAgent,Action: Iteration Loop
        
        InstaAgent->>+Memory: 3. get_context_dict()
        Memory-->>-InstaAgent: context dictionary
        
        InstaAgent->>+Perception: 4. process_input(SYSTEM_PROMPT, current_query, context)
        Perception-->>-InstaAgent: parsed_response
        
        InstaAgent->>+Decision: 5. determine_next_action(parsed_response, memory, usernames)
        Decision-->>-InstaAgent: action_type, action_params
        
        alt action_type == "function_call" or action_type == "mixed"
            rect rgb(255, 245, 225)
                InstaAgent->>+Action: 6a. execute_function(function_name, params)
                Action-->>-InstaAgent: result
                
                alt function_name == "get_user_metrics"
                    rect rgb(240, 255, 240)
                        InstaAgent->>+Memory: 7a. store_user_metrics(result)
                        Memory-->>-InstaAgent: updated memory
                    end
                else function_name == "calculate_user_score"
                    rect rgb(240, 240, 255)
                        InstaAgent->>+Memory: 7b. store_user_score(result["username"], result.get("score", 0))
                        Memory-->>-InstaAgent: updated memory
                    end
                else function_name == "rank_users"
                    rect rgb(255, 240, 245)
                        InstaAgent->>+Memory: 7c. update_users_list(result)
                        Memory-->>-InstaAgent: updated memory
                    end
                end
            end
            
        else action_type == "final_answer"
            rect rgb(245, 230, 230)
                InstaAgent->>+Action: 6b. format_final_results(ranked_users, verbose)
                Action-->>-InstaAgent: formatted results
                InstaAgent-->>Client: 7d. return ranked_users
            end
        end
        
        InstaAgent->>+Action: 8. format_iteration_response(iteration, action_type, action_params)
        Action-->>-InstaAgent: response_text
        
        InstaAgent->>+Memory: 9. add_iteration_response(response_text)
        Memory-->>-InstaAgent: updated memory
    end
    
    alt max_iterations reached without final_answer
        rect rgb(255, 235, 235)
            InstaAgent->>+Memory: 10. get_all_users_metrics()
            Memory-->>-InstaAgent: all_users_metrics
            InstaAgent-->>Client: 11. return all_users_metrics
        end
    end
```
## Setup and Installation

### Prerequisites

- Python 3.8+
- Ollama (for local model support)
- Instagram account credentials
- Google API key (for Gemini model)

### Installation

1. ***Clone the repository:***

```bash
git clone <repository-url>
cd instoma_backend
```

2. ***Install dependencies:***

`pip install -r requirements.txt`


3. ***Set up environment variables:***
```bash
cp .env.example .env
```
Update the .env file with your configuration.

4. ***Run the FastAPI application:***
```bash
python mainv1.py
```


# Project Structure
``` bash
instoma_backend/
├── ai/
│   ├── __init__.py
│   ├── agents/
│   │   ├── instagram_tools/
│   │   │   ├── action.py         # Action layer for Instagram agent
│   │   │   ├── decision.py       # Decision layer for Instagram agent
│   │   │   ├── insta_agent.py    # Main orchestration for Instagram agent
│   │   │   ├── instagram_tools.py # Instagram API wrapper functions
│   │   │   ├── memory.py         # Memory layer for Instagram agent
│   │   │   └── perception.py     # Perception layer for Instagram agent
│   │   └── instagram_tools_models/ # Pydantic models for Instagram tools
│   ├── config.py                 # AI configuration settings
│   ├── model_factory.py          # Factory for creating AI models
│   ├── models/                   # AI model implementations
│   │   ├── base.py               # Base interface for AI models
│   │   ├── google_gemini.py      # Google Gemini implementation
│   │   └── vision_trial_llama.py # Llama vision model implementation
│   └── router.py                 # FastAPI router for AI endpoints
├── routers/
│   └── instagram.py              # FastAPI router for Instagram endpoints
├── social/
│   └── instagram.py              # Instagram client implementation
├── utils/
│   ├── image_processing.py       # Image processing utilities
│   └── logger.py                 # Logging utilities
├── .env.example                  # Example environment variables
├── mainv1.py                     # Main FastAPI application
└── requirements.txt              # Project dependencies

```

## API Endpoints
### AI Endpoints
- `POST /ai/generate-caption-hashtags` : Generate captions and hashtags for an image
- `POST /ai/analyze-instagram-users `: Analyze and rank Instagram users based on metrics
### Instagram Endpoints
- `POST /instagram/post`: Post content to Instagram
- `GET /instagram/account-info` : Get information about the connected Instagram account
