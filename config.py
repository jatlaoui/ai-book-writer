# --- config.py ---
"""HACK: Force OpenAI api_type, but use Google Gemini API Key and Endpoint"""
import os
from typing import Dict, List, Optional

def get_config(use_google_gemini: bool = False, temperature_writer: float = 0.7, temperature_editor: float = 0.7, temperature_planner: float = 0.7, default_tone: str = "غامضة ومثيرة للتفكير", target_arabic_writers: Optional[List[str]] = None, target_world_writers: Optional[List[str]] = None) -> Dict:
    """HACK: Force OpenAI api_type, but use Google Gemini API Key and Endpoint."""

    # HACK: Force OpenAI api_type, but use Google Gemini API Key and Endpoint
    use_google_gemini = False # Force use_google_gemini to False - we are tricking it into using OpenAI client
    config_list = [{
        'api_type': 'openai', # Force api_type to 'openai' - TRICKING AUTOGEN
        'model': 'gpt-3.5-turbo',  # Model - might be ignored, but set to OpenAI model
        'api_key': os.getenv("GOOGLE_API_KEY", "AIzaSyDOrc8BFLoH3080xoDiDRk7qJYVEbMmgD4"),  # Use GOOGLE_API_KEY env var, but as "OpenAI key" - HACK
        'base_url': 'https://generativelanguage.googleapis.com/v1', # Set base_url to Gemini API endpoint - HACK
        'temperature': 0.7,
    }]


    # Chapter length enforcement instructions
    chapter_length_requirement = """
    **Chapter Length Requirements (متطلبات طول الفصل)**
    1. Each chapter must target at least 5000 words على الأقل.
    2. If a chapter is shorter than 3000 words, return it to the writer for expansion.
    3. This is a hard requirement - do not approve chapters shorter than 3000 words.
    """

    # Common agent configuration
    agent_config = {
        "seed": 42,
        "temperature": 0.7,
        "config_list": config_list,
        "timeout": 600,
        "cache_seed": None,
        "system_message": f"You are a professional book author writing in Arabic, following Jitlawi Developed Style. {chapter_length_requirement}",
        "max_consecutive_auto_reply": 10,
        "human_input_mode": "TERMINATE",
        "api_type": "openai", # Force api_type in agent_config as well - HACK
    }

    agent_config["default_tone"] = default_tone
    agent_config["target_arabic_writers"] = target_arabic_writers
    agent_config["target_world_writers"] = target_world_writers
    return agent_config
