#!/usr/bin/env python3
"""
Standalone service runner for AltGrammarly.
Does NOT start the menu bar app - only processes text.
"""
import sys
import os
import warnings
import logging
import time
from datetime import datetime

# Suppress all warnings
warnings.filterwarnings('ignore')

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, 'service.log')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler(sys.stderr)  # Also log to stderr for Automator
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("SERVICE RUNNER STARTED")
logger.info("=" * 60)

# Load environment
logger.info(f"Script directory: {script_dir}")
logger.info("Loading .env file...")
from dotenv import load_dotenv
env_file = os.path.join(script_dir, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
    logger.info(f"✓ Loaded .env from: {env_file}")
else:
    logger.warning(f"⚠ .env file not found at: {env_file}")

# Check API key
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    logger.info(f"✓ API key found: {api_key[:8]}...{api_key[-4:]}")
else:
    logger.error("✗ GEMINI_API_KEY not found in environment")

# Import only what we need - avoid importing main.py or anything that starts the app
logger.info("Importing Google Genai SDK...")
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import ClientError
    logger.info("✓ Successfully imported Genai SDK")
except Exception as e:
    logger.error(f"✗ Failed to import Genai SDK: {e}")
    sys.exit(1)

class StandaloneGeminiClient:
    """Minimal Gemini client for services - no menu bar dependencies."""
    
    SYSTEM_INSTRUCTION_CORRECT = (
        "You are an expert technical editor. Correct the grammar and improve the "
        "clarity of the following text while maintaining a professional, "
        "software-engineer-friendly tone. Return ONLY the corrected text without "
        "any explanations, comments, or markdown formatting."
    )
    
    SYSTEM_INSTRUCTION_SHORTEN = (
        "You are an expert technical editor. Make the following text more succinct "
        "and to-the-point while correcting any grammar errors. Maintain a warm, human "
        "touch and keep it professional but conversational - avoid sounding brusque or "
        "overly mechanical. Preserve the core message and maintain a software-engineer-friendly "
        "tone. Return ONLY the shortened and corrected text without any explanations, "
        "comments, or markdown formatting."
    )
    
    SYSTEM_INSTRUCTION_REPHRASE = (
        "You are an expert technical editor. Rephrase the following text to improve "
        "clarity and flow while maintaining the same meaning and tone. Use different "
        "words and sentence structures but keep the professional, software-engineer-friendly "
        "style. Return ONLY the rephrased text without any explanations, comments, or "
        "markdown formatting."
    )
    
    SYSTEM_INSTRUCTION_FORMAL = (
        "You are an expert technical editor. Rewrite the following text in a more formal "
        "and professional tone suitable for business communication or official documentation. "
        "Maintain clarity and precision while elevating the language. Remove any casual "
        "expressions or slang. Return ONLY the formalized text without any explanations, "
        "comments, or markdown formatting."
    )
    
    SYSTEM_INSTRUCTION_RESPECTFUL = (
        "You are an expert technical editor. Rewrite the following text to be more "
        "respectful, considerate, and diplomatic. Soften any harsh language while "
        "maintaining the core message. Use polite phrasing and show empathy. Keep it "
        "professional and software-engineer-friendly. Return ONLY the respectful version "
        "without any explanations, comments, or markdown formatting."
    )
    
    SYSTEM_INSTRUCTION_POSITIVE = (
        "You are an expert technical editor. Rewrite the following text to convey the "
        "message in a more positive and constructive way, even if the original sentiment "
        "is negative or critical. Use tactful language that focuses on solutions and "
        "improvements rather than problems. Maintain professionalism and a software-engineer-friendly "
        "tone. Return ONLY the positively framed text without any explanations, comments, "
        "or markdown formatting."
    )
    
    def __init__(self):
        logger.info("Initializing StandaloneGeminiClient...")
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in environment")
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        logger.info(f"Configuring Genai client with key: {self.api_key[:8]}...{self.api_key[-4:]}")
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = 'gemini-1.5-flash'
        logger.info(f"✓ Client initialized with model: {self.model_id}")
    
    def _process_text(self, text, system_instruction):
        """Process text with Gemini API with exponential backoff."""
        logger.info(f"Processing text (length: {len(text)} chars)...")
        prompt = f"{system_instruction}\n\nText to process:\n{text}"
        
        # Exponential backoff configuration
        max_retries = 5
        base_delay = 1.0  # Start with 1 second
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Sending request to Gemini API... (attempt {attempt + 1}/{max_retries})")
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            include_thoughts=False,
                            thinking_budget=100
                        ),
                        temperature=1.0
                    )
                )
                
                if not response or not response.text:
                    logger.error("No response from API")
                    raise Exception("No response from API")
                
                result = response.text.strip()
                logger.info(f"✓ Received response (length: {len(result)} chars)")
                return result
            
            except ClientError as e:
                # Handle rate limiting (429) with exponential backoff
                status_code = getattr(e, 'status_code', None) or getattr(e, 'code', None)
                
                if status_code == 429:
                    if attempt < max_retries - 1:
                        # Calculate exponential backoff: 1s, 2s, 4s, 8s, 16s
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"⚠️ Rate limit hit (429). Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} retries")
                        raise Exception(
                            "Gemini API rate limit exceeded. Please wait and try again. "
                            "Free tier: 20 requests/day."
                        )
                else:
                    # Other client errors (4xx)
                    logger.error(f"API client error: {str(e)}")
                    raise Exception(f"Gemini API error: {str(e)}")
            
            except Exception as e:
                # Non-ClientError exceptions
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"⚠️ Request failed: {str(e)}. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Request failed after {max_retries} retries: {str(e)}")
                    raise
    
    def correct_text(self, text):
        """Correct grammar and style."""
        return self._process_text(text, self.SYSTEM_INSTRUCTION_CORRECT)
    
    def shorten_text(self, text):
        """Shorten and correct text."""
        return self._process_text(text, self.SYSTEM_INSTRUCTION_SHORTEN)
    
    def rephrase_text(self, text):
        """Rephrase text for better clarity."""
        return self._process_text(text, self.SYSTEM_INSTRUCTION_REPHRASE)
    
    def formalize_text(self, text):
        """Make text more formal."""
        return self._process_text(text, self.SYSTEM_INSTRUCTION_FORMAL)
    
    def respectful_text(self, text):
        """Make text more respectful."""
        return self._process_text(text, self.SYSTEM_INSTRUCTION_RESPECTFUL)
    
    def positive_text(self, text):
        """Frame text more positively."""
        return self._process_text(text, self.SYSTEM_INSTRUCTION_POSITIVE)


def main():
    logger.info(f"Arguments: {sys.argv}")
    
    if len(sys.argv) < 2:
        logger.error("Missing operation argument")
        print("Error: Missing operation argument", file=sys.stderr)
        sys.exit(1)
    
    operation = sys.argv[1]
    logger.info(f"Operation: {operation}")
    
    # Read text from stdin
    logger.info("Reading text from stdin...")
    text = sys.stdin.read()
    logger.info(f"Received text: {len(text)} characters")
    logger.info(f"Text preview: '{text[:100]}{'...' if len(text) > 100 else ''}'")
    
    if not text.strip():
        logger.error("No text provided or text is empty")
        print("Error: No text provided", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialize standalone client (no menu bar app)
        logger.info("Creating StandaloneGeminiClient...")
        client = StandaloneGeminiClient()
        
        # Process text
        logger.info(f"Processing text with operation: {operation}")
        if operation == "correct":
            result = client.correct_text(text)
        elif operation == "shorten":
            result = client.shorten_text(text)
        elif operation == "rephrase":
            result = client.rephrase_text(text)
        elif operation == "formal":
            result = client.formalize_text(text)
        elif operation == "respectful":
            result = client.respectful_text(text)
        elif operation == "positive":
            result = client.positive_text(text)
        else:
            logger.error(f"Unknown operation: {operation}")
            print(f"Error: Unknown operation '{operation}'", file=sys.stderr)
            sys.exit(1)
        
        # Output result
        logger.info(f"Outputting result: {len(result)} characters")
        logger.info(f"Result preview: '{result[:100]}{'...' if len(result) > 100 else ''}'")
        print(result, end='')
        logger.info("=" * 60)
        logger.info("SERVICE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
