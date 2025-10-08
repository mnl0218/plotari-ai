"""
Service for OpenAI model management
Handles model availability checks and model information
"""
from typing import List, Dict, Any
from .interfaces import OpenAIModelInterface
from .connection_service import OpenAIConnectionService
import logging

logger = logging.getLogger(__name__)


class OpenAIModelService(OpenAIModelInterface):
    """Service for handling OpenAI model management"""
    
    def __init__(self, connection_service: OpenAIConnectionService):
        self.connection_service = connection_service
    
    def is_available(self) -> bool:
        """Checks if OpenAI service is available"""
        try:
            # Make a simple call to verify connection
            client = self.connection_service.get_client()
            client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI not available: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Returns list of available models"""
        try:
            client = self.connection_service.get_client()
            models = client.models.list()
            return self._filter_relevant_models(models.data)
        except Exception as e:
            logger.error(f"Error getting models: {e}")
            return []
    
    def _check_api_connection(self) -> bool:
        """Internal method to check API connection"""
        try:
            client = self.connection_service.get_client()
            client.models.list()
            return True
        except Exception:
            return False
    
    def _filter_relevant_models(self, models: List[Any]) -> List[str]:
        """Filters models to only include relevant ones (GPT and embedding models)"""
        try:
            relevant_models = []
            for model in models:
                model_id = getattr(model, 'id', '')
                if 'gpt' in model_id or 'embedding' in model_id:
                    relevant_models.append(model_id)
            return relevant_models
        except Exception as e:
            logger.error(f"Error filtering models: {e}")
            return []
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Gets detailed information about a specific model"""
        try:
            client = self.connection_service.get_client()
            models = client.models.list()
            
            for model in models.data:
                if getattr(model, 'id', '') == model_id:
                    return {
                        "id": model.id,
                        "object": getattr(model, 'object', ''),
                        "created": getattr(model, 'created', None),
                        "owned_by": getattr(model, 'owned_by', ''),
                        "permission": getattr(model, 'permission', [])
                    }
            
            return {}
        except Exception as e:
            logger.error(f"Error getting model info for {model_id}: {e}")
            return {}
