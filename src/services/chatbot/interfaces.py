"""
Interfaces/Protocols for chatbot services
Defines clear contracts between different services
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.models.property import Property, POI, ChatRequest, ChatResponse


class IntentExtractorInterface(ABC):
    """Interface for search intent extraction"""
    
    @abstractmethod
    def extract_search_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts search intent from a message"""
        pass


class PropertySearchInterface(ABC):
    """Interface for property searches"""
    
    @abstractmethod
    def search_properties(self, search_intent: Dict[str, Any]) -> List[Property]:
        """Searches properties based on intent"""
        pass
    
    @abstractmethod
    def get_property_detail(self, search_intent: Dict[str, Any]) -> Optional[Any]:
        """Gets property detail"""
        pass
    
    @abstractmethod
    def compare_properties(self, search_intent: Dict[str, Any]) -> List[Property]:
        """Compares properties"""
        pass


class POISearchInterface(ABC):
    """Interface for POI searches"""
    
    @abstractmethod
    def search_pois(self, search_intent: Dict[str, Any]) -> List[POI]:
        """Searches POIs based on intent"""
        pass


class ResponseGeneratorInterface(ABC):
    """Interface for response generation"""
    
    @abstractmethod
    def generate_response(self, message: str, properties: List[Property], pois: List[POI], 
                         search_intent: Dict[str, Any], conversation: Optional[Dict[str, Any]] = None) -> str:
        """Generates a contextual response"""
        pass


class ConversationManagerInterface(ABC):
    """Interface for conversation management"""
    
    @abstractmethod
    def get_or_create_conversation(self, session_id: str) -> Dict[str, Any]:
        """Gets or creates a conversation"""
        pass
    
    @abstractmethod
    def build_context_from_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Builds context from conversation"""
        pass
    
    @abstractmethod
    def update_conversation_context(self, conversation: Dict[str, Any], search_intent: Dict[str, Any], 
                                   properties_found: List[Property]) -> None:
        """Updates conversation context"""
        pass
    
    @abstractmethod
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets conversation history"""
        pass
    
    @abstractmethod
    def clear_conversation(self, session_id: str) -> bool:
        """Clears a specific conversation"""
        pass


class CacheManagerInterface(ABC):
    """Interface for cache management"""
    
    @abstractmethod
    def add_to_memory_cache(self, session_id: str, conversation: Dict[str, Any]) -> None:
        """Adds conversation to memory cache"""
        pass
    
    @abstractmethod
    def save_conversation_to_cache(self, session_id: str, conversation: Dict[str, Any]) -> None:
        """Saves conversation to JSON cache"""
        pass
    
    @abstractmethod
    def cleanup_old_conversations(self) -> None:
        """Cleans old conversations"""
        pass
    
    @abstractmethod
    def get_cache_info(self) -> Dict[str, Any]:
        """Gets cache information"""
        pass
    
    @abstractmethod
    def clear_all_cache(self) -> Dict[str, Any]:
        """Clears all cache"""
        pass
