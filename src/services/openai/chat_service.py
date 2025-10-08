"""
Service for OpenAI chat completion operations
Handles chat completion and conversation management
"""
from typing import List, Dict
from .interfaces import OpenAIChatInterface
from .connection_service import OpenAIConnectionService
import logging

logger = logging.getLogger(__name__)


class OpenAIChatService(OpenAIChatInterface):
    """Service for handling OpenAI chat completion operations"""
    
    def __init__(self, connection_service: OpenAIConnectionService):
        self.connection_service = connection_service
    
    def generate_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generates chat response using OpenAI"""
        try:
            if not self._validate_messages(messages):
                raise ValueError("Message list cannot be empty or invalid")
            
            client = self.connection_service.get_client()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            logger.debug(f"Response generated with {len(content)} characters")
            return content
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise
    
    def _validate_messages(self, messages: List[Dict[str, str]]) -> bool:
        """Validates message structure for chat completion"""
        if not messages:
            return False
        
        for message in messages:
            if not isinstance(message, dict) or "role" not in message or "content" not in message:
                return False
        
        return True
    
    def _call_chat_completion_api(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Internal method to call OpenAI chat completion API"""
        try:
            client = self.connection_service.get_client()
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling chat completion API: {e}")
            raise
