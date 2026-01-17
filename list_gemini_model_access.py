import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

print("Check available models for my api key...")
print("-" * 50)

# list all models
for model in client.models.list():
    print(f"ID: {model.name}")
    print(f"Supported Action: {model.supported_actions}")
    print("-" * 50)

# Check for Gemini 3 specifically
has_g3 = any("gemini-3-flash" in m.name for m in client.models.list())
if has_g3:
    print("Success: have access to gemini 3 flash")
else:
    print("Notice: Gemini 3 Flash is not yet in the list")
