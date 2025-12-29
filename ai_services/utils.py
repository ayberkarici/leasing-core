"""
AI Services utilities.
Helper functions for AI operations.
"""

import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
    
    Usage:
        @retry_with_backoff(max_retries=3)
        def my_api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def truncate_text(text: str, max_length: int = 4000) -> str:
    """
    Truncate text to a maximum length while trying to preserve meaning.
    
    Args:
        text: Text to truncate
        max_length: Maximum length in characters
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Try to truncate at a sentence boundary
    truncated = text[:max_length]
    
    # Find last sentence end
    for end_char in ['. ', '! ', '? ', '\n']:
        last_end = truncated.rfind(end_char)
        if last_end > max_length * 0.8:  # At least 80% of content
            return truncated[:last_end + 1].strip()
    
    # Fallback to word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.9:
        return truncated[:last_space].strip() + "..."
    
    return truncated.strip() + "..."


def calculate_token_estimate(text: str) -> int:
    """
    Estimate the number of tokens in a text.
    Rough estimation: ~4 characters per token for English,
    ~2-3 characters per token for Turkish.
    
    Args:
        text: Text to estimate tokens for
    
    Returns:
        Estimated token count
    """
    # Turkish text tends to have more tokens per word
    # Using a conservative estimate of 3 chars per token
    return len(text) // 3


def format_currency(amount: float, currency: str = "TL") -> str:
    """
    Format a number as currency.
    
    Args:
        amount: Amount to format
        currency: Currency symbol
    
    Returns:
        Formatted currency string
    """
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} {currency}"


def clean_ai_response(response: str) -> str:
    """
    Clean AI response by removing markdown and extra whitespace.
    
    Args:
        response: Raw AI response
    
    Returns:
        Cleaned response
    """
    import re
    
    # Remove markdown code blocks
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*', '', response)
    
    # Remove excessive whitespace
    response = re.sub(r'\n{3,}', '\n\n', response)
    response = response.strip()
    
    return response


def extract_json_from_response(response: str) -> Optional[dict]:
    """
    Extract JSON object from AI response.
    Handles cases where JSON is embedded in text.
    
    Args:
        response: AI response text
    
    Returns:
        Parsed JSON object or None
    """
    import json
    
    # Clean the response first
    cleaned = clean_ai_response(response)
    
    # Try direct parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON object
    json_start = cleaned.find('{')
    json_end = cleaned.rfind('}')
    
    if json_start != -1 and json_end > json_start:
        try:
            return json.loads(cleaned[json_start:json_end + 1])
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON array
    json_start = cleaned.find('[')
    json_end = cleaned.rfind(']')
    
    if json_start != -1 and json_end > json_start:
        try:
            return json.loads(cleaned[json_start:json_end + 1])
        except json.JSONDecodeError:
            pass
    
    return None


class AIFallbackHandler:
    """
    Handler for AI service fallbacks.
    Provides manual alternatives when AI is unavailable.
    """
    
    @staticmethod
    def document_validation_fallback() -> dict:
        """
        Fallback response for document validation.
        Indicates manual review is needed.
        """
        return {
            "is_valid": None,
            "confidence_score": 0,
            "manual_review_required": True,
            "message": "AI servisi kullanılamıyor. Manuel inceleme gerekiyor.",
            "found_fields": [],
            "missing_fields": [],
            "warnings": ["AI validasyonu yapılamadı"]
        }
    
    @staticmethod
    def task_prioritization_fallback(tasks: list) -> dict:
        """
        Fallback for task prioritization.
        Returns tasks sorted by creation date.
        """
        return {
            "prioritized_tasks": [
                {"task_id": t.id, "priority_score": 50, "reasoning": "Manuel önceliklendirme gerekli"}
                for t in tasks
            ],
            "focus_recommendation": "AI servisi kullanılamıyor. Görevleri manuel olarak önceliklendirin.",
            "manual_required": True
        }
    
    @staticmethod
    def proposal_generation_fallback() -> dict:
        """
        Fallback for proposal generation.
        """
        return {
            "title": "Leasing Teklifi",
            "sections": [],
            "summary": "AI servisi kullanılamıyor. Teklifi manuel olarak oluşturun.",
            "manual_required": True
        }

