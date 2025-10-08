"""
Main OpenAI service - Refactored
Orchestrates all specialized OpenAI services
"""
from typing import List, Dict, Any, Optional
from src.models.property import Property, POI
from .connection_service import OpenAIConnectionService
from .embedding_service import OpenAIEmbeddingService
from .chat_service import OpenAIChatService
from .intent_extraction_service import OpenAIIntentExtractionService
from .property_response_service import OpenAIPropertyResponseService
from .summary_service import OpenAISummaryService
from .model_service import OpenAIModelService
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    """Main OpenAI service - Refactored"""
    
    def __init__(self):
        # Initialize specialized services
        self.connection_service = OpenAIConnectionService()
        self.embedding_service = OpenAIEmbeddingService(self.connection_service)
        self.chat_service = OpenAIChatService(self.connection_service)
        self.model_service = OpenAIModelService(self.connection_service)
        
        # Initialize services that depend on the above
        self.intent_extraction_service = OpenAIIntentExtractionService(
            self.connection_service, 
            self.chat_service
        )
        self.property_response_service = OpenAIPropertyResponseService(
            self.connection_service, 
            self.chat_service
        )
        self.summary_service = OpenAISummaryService(
            self.connection_service, 
            self.chat_service
        )
        
        logger.info("OpenAIService refactored initialized successfully")
    
    def generate_embeddings(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Generates embeddings for given text"""
        return self.embedding_service.generate_embeddings(text, model)
    
    def generate_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generates chat response using OpenAI"""
        return self.chat_service.generate_chat_completion(messages, model, temperature, max_tokens)
    
    def extract_search_intent(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts search intent from user message using OpenAI"""
        return self.intent_extraction_service.extract_search_intent(user_message, context)
    
    def generate_property_response(
        self, 
        user_message: str, 
        properties: List[Property], 
        pois: List[POI] = None,
        search_intent: Dict[str, Any] = None
    ) -> str:
        """Generates a contextual response about found properties"""
        return self.property_response_service.generate_property_response(
            user_message, properties, pois, search_intent
        )
    
    def generate_chat_summary(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generates a summary of the user's first message and context"""
        return self.summary_service.generate_chat_summary(user_message, context)
    
    def is_available(self) -> bool:
        """Checks if OpenAI service is available"""
        return self.model_service.is_available()
    
    def get_available_models(self) -> List[str]:
        """Returns list of available models"""
        return self.model_service.get_available_models()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # OpenAI client doesn't need explicit closing
        pass
