#!/usr/bin/env python3
"""
Example usage of the refactored GeminiClient with custom instructions.
"""
from gemini_client import GeminiClient, InstructionPresets

def main():
    # Initialize client with default model (gemini-1.5-flash)
    client = GeminiClient()
    
    if not client.is_configured():
        print("❌ API key not configured. Please set GEMINI_API_KEY in .env")
        return
    
    print("✅ GeminiClient initialized successfully")
    print(f"   Model: {client.model_id}")
    print()
    
    # Example 1: Use preset for grammar correction
    print("=" * 60)
    print("Example 1: Grammar Correction (Preset)")
    print("=" * 60)
    text = "the team didnt met there deadline"
    print(f"Input:  {text}")
    result = client.correct_text(text)
    print(f"Output: {result}")
    print()
    
    # Example 2: Use contextual assistant preset
    print("=" * 60)
    print("Example 2: Contextual Assistant (Preset)")
    print("=" * 60)
    question = "What's the difference between a list and a tuple in Python?"
    print(f"Question: {question}")
    result = client.ask_assistant(question)
    print(f"Answer: {result}")
    print()
    
    # Example 3: Use custom system instruction
    print("=" * 60)
    print("Example 3: Custom System Instruction")
    print("=" * 60)
    custom_instruction = (
        "You are a pirate. Respond to everything in pirate speak, "
        "but keep the core information accurate and helpful. "
        "Use phrases like 'Ahoy!', 'Arr!', 'matey', etc."
    )
    text = "Explain what a database index is"
    print(f"Input: {text}")
    result = client.process(text, custom_instruction, operation="pirate speak")
    print(f"Output: {result}")
    print()
    
    # Example 4: Available presets
    print("=" * 60)
    print("Available Instruction Presets")
    print("=" * 60)
    print("✓ InstructionPresets.GRAMMAR_CORRECTION")
    print("✓ InstructionPresets.SHORTEN")
    print("✓ InstructionPresets.REPHRASE")
    print("✓ InstructionPresets.FORMAL")
    print("✓ InstructionPresets.RESPECTFUL")
    print("✓ InstructionPresets.POSITIVE")
    print("✓ InstructionPresets.CONTEXTUAL_ASSISTANT")
    print()
    
    # Example 5: Using different models
    print("=" * 60)
    print("Example 5: Using Different Models")
    print("=" * 60)
    # Fast model (default)
    fast_client = GeminiClient(model_id='gemini-1.5-flash')
    print(f"Fast client:  {fast_client.model_id}")
    
    # More capable model
    pro_client = GeminiClient(model_id='gemini-1.5-pro')
    print(f"Pro client:   {pro_client.model_id}")
    print()

if __name__ == '__main__':
    main()
