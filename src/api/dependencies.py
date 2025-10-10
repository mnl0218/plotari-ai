"""
API dependencies
Provides dependency injection for services
"""
from src.services.sync import PropertySyncService
from src.services.weaviate import WeaviateDeletionService, WeaviateService
from src.services.chatbot import ChatbotService

def get_sync_service() -> PropertySyncService:
    """Dependency to get the property sync service"""
    return PropertySyncService()

def get_deletion_service() -> WeaviateDeletionService:
    """Dependency to get the weaviate deletion service"""
    return WeaviateDeletionService()

def get_chatbot_service() -> ChatbotService:
    """Dependency to get the chatbot service"""
    return ChatbotService()

def get_weaviate_service() -> WeaviateService:
    """Dependency to get the weaviate service"""
    return WeaviateService()