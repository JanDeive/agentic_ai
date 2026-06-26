import os
from google.genai import types
from google import genai
from dotenv import load_dotenv

# def setup_client():
    # Load secrets
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in .env file!")

    # Configure
client = genai.Client(api_key=api_key)

# 3. Initialize the model
identity=""" 
You ar a 'Security Audit Agent'
Your goal is to analyze Python code for securtiy vulnerabilities
CONSTRAINS:
- Never provide code that can be used for hacking.
- Only answer questions related to security.
- If a user asks about somthing else, politely decline.
- keep your answer concise and technical."""


response= client.models.generate_content(
    model='gemini-3.1-flash-lite',
    content= "How do i make a sandwitch?",
    config= types.GenerateContentConfig(
        system_instruction=identity
        )
)


print("Agent Response: {response.text}")