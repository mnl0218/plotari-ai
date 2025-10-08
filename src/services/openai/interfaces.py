"""
Interfaces/Protocols for OpenAI services
Defines clear contracts between different OpenAI services
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.models.property import Property, POI

class OpenAIConnectionInterface(ABC):
    """Interface for OpenAI connection management"""
    
    @abstractmethod
    def get_client(self) -> Any:
        """Gets the OpenAI client instance"""
        pass

class OpenAIEmbeddingInterface(ABC):
    """Interface for OpenAI embedding operations"""
    
    @abstractmethod
    def generate_embeddings(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Generates embeddings for given text"""
        pass

class OpenAIChatInterface(ABC):
    """Interface for OpenAI chat completion operations"""
    
    @abstractmethod
    def generate_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generates chat response using OpenAI"""
        pass

class OpenAIIntentExtractionInterface(ABC):
    """Interface for OpenAI intent extraction operations"""
    
    @abstractmethod
    def extract_search_intent(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts search intent from user message using OpenAI"""
        pass

class OpenAIPropertyResponseInterface(ABC):
    """Interface for OpenAI property response generation"""
    
    @abstractmethod
    def generate_property_response(
        self, 
        user_message: str, 
        properties: List[Property], 
        pois: List[POI] = None,
        search_intent: Dict[str, Any] = None
    ) -> str:
        """Generates a contextual response about found properties"""
        pass

class OpenAISummaryInterface(ABC):
    """Interface for OpenAI summary generation operations"""
    
    @abstractmethod
    def generate_chat_summary(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generates a summary of the user's first message and context"""
        pass

class OpenAIModelInterface(ABC):
    """Interface for OpenAI model management"""
    
    @abstractmethod
    def is_available(self) -> bool:
        """Checks if OpenAI service is available"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Returns list of available models"""
        pass
