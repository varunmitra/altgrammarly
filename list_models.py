#!/usr/bin/env python3
"""List available Gemini models"""
import os
from dotenv import load_dotenv
from google import genai

# Load API key
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

if not api_key:
    print("No API key found!")
    exit(1)

print(f"Using API key: {api_key[:8]}...{api_key[-4:]}\n")

# Initialize client
client = genai.Client(api_key=api_key)

print("Fetching available models...\n")
print("=" * 60)

try:
    # List models
    models = client.models.list()
    
    print("Available models that support generateContent:\n")
    for model in models:
        model_name = model.name
        # Check if it supports generateContent
        if hasattr(model, 'supported_generation_methods'):
            if 'generateContent' in model.supported_generation_methods:
                print(f"✓ {model_name}")
        else:
            print(f"  {model_name}")
    
except Exception as e:
    print(f"Error: {e}")
    
print("\n" + "=" * 60)
