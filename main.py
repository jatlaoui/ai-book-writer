# --- main.py ---
"""Direct Google Gemini API Test - Bypassing config.py"""
import autogen
import os

def main():
    print("Starting Direct Gemini API Test...")

    # --- Configuration - Hardcoded for Google Gemini Direct Test ---
    config_list_gemini = [{
        'api_type': 'google_gemini',
        'model': 'gemini-pro',
        'api_key': os.getenv("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY"), # Ensure GOOGLE_API_KEY env variable is set
    }]

    # --- Create a Google Gemini AssistantAgent Directly ---
    gemini_agent = autogen.AssistantAgent(
        name="gemini_test_agent",
        llm_config={
            "config_list": config_list_gemini,
            "temperature": 0.7,
        }
    )

    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="TERMINATE",
        code_execution_config=False
    )

    # --- Test Interaction ---
    user_proxy.initiate_chat(
        gemini_agent,
        message="Write a very short poem about a cat in Arabic.", # Simple Arabic prompt
    )

    print("\nDirect Gemini API Test Completed.")

if __name__ == "__main__":
    main()
