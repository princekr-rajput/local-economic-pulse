"""
Quick test to verify Gemini API key is working (new google-genai SDK).
"""

import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env file")
    exit()

# Create client
client = genai.Client(api_key=api_key)

# Generate response
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Say hello and confirm you're working, in one short sentence."
)

print("Response from Gemini:")
print(response.text)