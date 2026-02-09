"""
Gemini API client wrapper for text processing.
Optimized for speed with Gemini Flash models.
"""
import os
import logging
import time
from typing import Optional, Dict
from google import genai
from google.genai import types
from google.genai.errors import ClientError

logger = logging.getLogger(__name__)


class InstructionPresets:
    """Predefined system instruction presets for common use cases."""
    
    # Grammar and style editing presets
    GRAMMAR_CORRECTION = (
        "You are an expert technical editor. Correct the grammar and improve the "
        "clarity of the following text while maintaining a professional, "
        "software-engineer-friendly tone. Return ONLY the corrected text without "
        "any explanations, comments, or markdown formatting."
    )
    
    SHORTEN = (
        "You are an expert technical editor. Make the following text more succinct "
        "and to-the-point while correcting any grammar errors. Maintain a warm, human "
        "touch and keep it professional but conversational - avoid sounding brusque or "
        "overly mechanical. Preserve the core message and maintain a software-engineer-friendly "
        "tone. Return ONLY the shortened and corrected text without any explanations, "
        "comments, or markdown formatting."
    )
    
    REPHRASE = (
        "You are an expert technical editor. Rephrase the following text to improve "
        "clarity and flow while maintaining the same meaning and tone. Use different "
        "words and sentence structures but keep the professional, software-engineer-friendly "
        "style. Return ONLY the rephrased text without any explanations, comments, or "
        "markdown formatting."
    )
    
    FORMAL = (
        "You are an expert technical editor. Rewrite the following text in a more formal "
        "and professional tone suitable for business communication or official documentation. "
        "Maintain clarity and precision while elevating the language. Remove any casual "
        "expressions or slang. Return ONLY the formalized text without any explanations, "
        "comments, or markdown formatting."
    )
    
    RESPECTFUL = (
        "You are an expert technical editor. Rewrite the following text to be more "
        "respectful, considerate, and diplomatic. Soften any harsh language while "
        "maintaining the core message. Use polite phrasing and show empathy. Keep it "
        "professional and software-engineer-friendly. Return ONLY the respectful version "
        "without any explanations, comments, or markdown formatting."
    )
    
    POSITIVE = (
        "You are an expert technical editor. Rewrite the following text to convey the "
        "message in a more positive and constructive way, even if the original sentiment "
        "is negative or critical. Use tactful language that focuses on solutions and "
        "improvements rather than problems. Maintain professionalism and a software-engineer-friendly "
        "tone. Return ONLY the positively framed text without any explanations, comments, "
        "or markdown formatting."
    )
    
    # General assistant preset
    CONTEXTUAL_ASSISTANT = (
        "You are a helpful, knowledgeable assistant. Provide clear, accurate, and "
        "contextually appropriate responses. Be concise but thorough. Use a friendly "
        "yet professional tone. When asked about technical topics, provide practical "
        "advice. Return your response without unnecessary preambles or explanations "
        "about your role."
    )
    
    # Backward compatibility aliases
    CORRECT = GRAMMAR_CORRECTION


class GeminiClient:
    """Generic wrapper for Google Gemini API with customizable system instructions."""
    
    def __init__(self, api_key: Optional[str] = None, model_id: str = 'gemini-1.5-flash'):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Gemini API key. If None, attempts to load from environment.
            model_id: Model to use. Defaults to 'gemini-1.5-flash' for speed.
                     Other options: 'gemini-1.5-pro', 'gemini-3-flash-preview'
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_id = model_id
        
        if not self.api_key:
            logger.warning("No API key found in environment")
            self.client = None
            return
            
        logger.info(f"Configuring Gemini API with key: {self.api_key[:8]}...{self.api_key[-4:]}")
        
        try:
            # Initialize Google Genai client
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"✓ Gemini client initialized with model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None
    
    def is_configured(self) -> bool:
        """Check if the API key is configured."""
        return self.api_key is not None and self.client is not None
    
    def process(self, text: str, system_instruction: str, operation: str = "processing") -> str:
        """
        Generic method to process text with a custom system instruction.
        
        Args:
            text: The text to be processed.
            system_instruction: The system instruction to guide the model.
            operation: Description of the operation (for logging).
            
        Returns:
            The processed text.
            
        Raises:
            ValueError: If API key is not configured or text is empty.
            Exception: If the API request fails.
        """
        return self._process_text(text, system_instruction, operation)
    
    # Convenience methods using presets
    def correct_text(self, text: str) -> str:
        """
        Send text to Gemini API for grammar and style correction.
        
        Args:
            text: The text to be corrected.
            
        Returns:
            The corrected text.
            
        Raises:
            ValueError: If API key is not configured or text is empty.
            Exception: If the API request fails.
        """
        return self._process_text(text, InstructionPresets.GRAMMAR_CORRECTION, "correction")
    
    def shorten_text(self, text: str) -> str:
        """
        Send text to Gemini API to make it more succinct.
        
        Args:
            text: The text to be shortened.
            
        Returns:
            The shortened text.
            
        Raises:
            ValueError: If API key is not configured or text is empty.
            Exception: If the API request fails.
        """
        return self._process_text(text, InstructionPresets.SHORTEN, "shortening")
    
    def rephrase_text(self, text: str) -> str:
        """Rephrase text for better clarity."""
        return self._process_text(text, InstructionPresets.REPHRASE, "rephrasing")
    
    def formalize_text(self, text: str) -> str:
        """Make text more formal and professional."""
        return self._process_text(text, InstructionPresets.FORMAL, "formalizing")
    
    def respectful_text(self, text: str) -> str:
        """Make text more respectful and diplomatic."""
        return self._process_text(text, InstructionPresets.RESPECTFUL, "making respectful")
    
    def positive_text(self, text: str) -> str:
        """Frame text more positively and constructively."""
        return self._process_text(text, InstructionPresets.POSITIVE, "making positive")
    
    def ask_assistant(self, text: str) -> str:
        """
        Use Gemini as a general-purpose contextual assistant.
        
        Args:
            text: The question or request.
            
        Returns:
            The assistant's response.
        """
        return self._process_text(text, InstructionPresets.CONTEXTUAL_ASSISTANT, "assistant query")
    
    def _process_text(self, text: str, system_instruction: str, operation: str) -> str:
        """
        Internal method to process text with Gemini API.
        
        Args:
            text: The text to be processed.
            system_instruction: The system instruction to use.
            operation: Description of the operation (for logging).
            
        Returns:
            The processed text.
            
        Raises:
            ValueError: If API key is not configured or text is empty.
            Exception: If the API request fails.
        """
        if not self.is_configured():
            logger.error("API key is not configured")
            raise ValueError("Gemini API key is not configured. Please set your API key first.")
        
        if not text or not text.strip():
            logger.error("Empty text provided")
            raise ValueError("No text provided for correction.")
        
        try:
            logger.info(f"Sending {operation} request to Gemini API... (text length: {len(text)} chars)")
            
            # Build the prompt with system instruction included
            prompt = f"{system_instruction}\n\nText to process:\n{text}"
            
            # Exponential backoff configuration
            max_retries = 5
            base_delay = 1.0  # Start with 1 second
            
            for attempt in range(max_retries):
                try:
                    # Optimized config for speed:
                    # - Flash model (already fastest available)
                    # - Low thinking_budget for quick responses
                    # - include_thoughts=False to exclude reasoning tokens
                    # - temperature=1.0 for balanced output
                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            thinking_config=types.ThinkingConfig(
                                include_thoughts=False,  # Don't include reasoning, just results
                                thinking_budget=100      # Minimal token budget for fast response
                            ),
                            temperature=1.0
                        )
                    )
                    
                    if not response or not response.text:
                        logger.error("Empty response from API")
                        raise Exception("No response received from Gemini API.")
                    
                    result = response.text.strip()
                    logger.info(f"✓ Response received ({len(result)} chars)")
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
                                "Gemini API rate limit exceeded. Please wait a few moments and try again. "
                                "Free tier: 20 requests/day. Consider upgrading your API plan."
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
                
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise Exception(f"Failed to get correction from Gemini API: {str(e)}")
    
    def update_api_key(self, new_api_key: str):
        """
        Update the API key and reconfigure the client.
        
        Args:
            new_api_key: The new API key to use.
        """
        self.api_key = new_api_key
        if not self.api_key:
            logger.warning("Empty API key provided")
            return
            
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("✓ API key updated successfully")
        except Exception as e:
            logger.error(f"Failed to update API key: {e}")
            self.client = None
