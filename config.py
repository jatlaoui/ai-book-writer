"""Configuration for the book generation system"""
import os
from typing import Dict, List

def get_config(use_deepseek: bool = True) -> Dict:
    """Get the configuration for the agents.
    
    Args:
        use_deepseek (bool): If True, use DeepSeek v3. If False, use ChatGPT.
    
    Returns:
        Dict: Configuration for AutoGen agents.
    """
    
    # Configuration for DeepSeek v3
    if use_deepseek:
        config_list = [{
            'model': 'deepseek-chat',
            'base_url': 'https://api.deepseek.com/v1',
            'api_key': os.getenv("sk-78ef53d55b03416fbbfb57d2991d43c8"),  # Ensure API key is set in environment
            'temperature': 0.7,
        }]
    # Configuration for ChatGPT (OpenAI)
    else:
        config_list = [{
            'model': 'gpt-4-1106-preview',  # Use GPT-4 Turbo (or 'gpt-3.5-turbo' for cheaper option)
            'api_key': os.getenv("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"),  # Ensure OpenAI API key is set in environment
            'base_url': 'https://api.openai.com/v1',  # OpenAI API endpoint
            'temperature': 0.7,
        }]

    # Chapter length enforcement instructions
    chapter_length_requirement = """
    **Chapter Length Requirements**
    1. Each chapter must target at least 5000 words.
    2. If a chapter is shorter than 3000 words, return it to the writer for expansion.
    3. This is a hard requirement - do not approve chapters shorter than 3000 words.
    """

    # Common configuration for all agents
    agent_config = {
        "seed": 42,
        "temperature": 0.7,
        "config_list": config_list,
        "timeout": 600,
        "cache_seed": None if not use_deepseek else 42,  # Enable caching only for DeepSeek
        "system_message": f"You are a professional book author. {chapter_length_requirement}",
        "max_consecutive_auto_reply": 10,  # Prevent infinite loops
        "human_input_mode": "TERMINATE",  # Allow human intervention if needed
    }
    
    return agent_config
