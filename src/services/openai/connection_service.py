"""
Service for OpenAI connection management
Handles API key validation and client initialization
"""
import openai
from typing import Any
import os
from dotenv import load_dotenv
from .interfaces import OpenAIConnectionInterface
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class OpenAIConnectionService(OpenAIConnectionInterface):
    """Service for handling OpenAI connection operations"""
    
    def __init__(self):
        self.api_key = None
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initializes the OpenAI client"""
        try:
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is not configured")
            
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("OpenAI connection service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing OpenAI connection: {e}")
            raise
    
    def get_client(self) -> Any:
        """Gets the OpenAI client instance"""
        if not self.client:
            self._initialize_client()
        return self.client
    
    def _validate_api_key(self) -> bool:
        """Validates the API key"""
        try:
            return self.api_key is not None and len(self.api_key.strip()) > 0
        except Exception:
            return False
    
    def is_connected(self) -> bool:
        """Checks if the service is properly connected"""
        try:
            return self._validate_api_key() and self.client is not None
        except Exception:
            return False
