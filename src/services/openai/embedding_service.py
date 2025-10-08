"""
Service for OpenAI embedding operations
Handles embedding generation and validation
"""
from typing import List
from .interfaces import OpenAIEmbeddingInterface
from .connection_service import OpenAIConnectionService
import logging

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService(OpenAIEmbeddingInterface):
    """Service for handling OpenAI embedding operations"""
    
    def __init__(self, connection_service: OpenAIConnectionService):
        self.connection_service = connection_service
    
    def generate_embeddings(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Generates embeddings for given text"""
        try:
            if not self._validate_text_input(text):
                raise ValueError("Text cannot be empty")
            
            client = self.connection_service.get_client()
            response = client.embeddings.create(
                input=text.strip(),
                model=model
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Embedding generated with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def _validate_text_input(self, text: str) -> bool:
        """Validates text input for embedding generation"""
        return text is not None and text.strip() != ""
    
    def _call_embedding_api(self, text: str, model: str) -> List[float]:
        """Internal method to call OpenAI embedding API"""
        try:
            client = self.connection_service.get_client()
            response = client.embeddings.create(
                input=text.strip(),
                model=model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error calling embedding API: {e}")
            raise
