# Instagram Automation Plugin (Instoma)

A powerful backend service for automating Instagram content creation and posting with AI-powered caption and hashtag generation.

## Overview

This project provides a FastAPI-based backend service that combines AI vision models with Instagram API integration to automate the process of creating and posting content to Instagram. The system can analyze images, generate engaging captions and relevant hashtags, and post directly to Instagram.

## Features

- **AI-Powered Caption Generation**: Analyze images and generate engaging captions using various AI models
- **Hashtag Recommendation**: Generate relevant hashtags for your content
- **Multiple AI Model Support**: 
  - Google Gemini
  - Llama (local)
  - Ollama integration
- **Instagram API Integration**: Post content directly to Instagram
- **Flexible Configuration**: Switch between different AI providers easily
## Setup and Installation

### Prerequisites

- Python 3.8+
- Ollama (for local model support)
- Instagram account credentials
- Google API key (for Gemini model)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd instoma_backend

2. Install dependencies:
pip install -r requirements.txt
```
3. Set up environment variables:
```bash
cp .env.example .env
```
Update the .env file with your configuration.
4. Run the FastAPI application:
```bash
python mainv1.py