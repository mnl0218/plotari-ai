"""
Service for search intent extraction
Handles intent detection and validation using OpenAI and rule-based fallback
"""
from typing import List, Dict, Any, Optional
from .interfaces import IntentExtractorInterface
from src.services.openai import OpenAIService
import logging
import re

logger = logging.getLogger(__name__)


class IntentExtractorService(IntentExtractorInterface):
    """Service for search intent extraction"""
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        self.openai_service = openai_service
    
    def extract_search_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts search intent from message and context using OpenAI as primary method"""
        try:
            # Try to use OpenAI as primary method
            if self.openai_service:
                try:
                    logger.info("🔍 Using OpenAI to extract search intent")
                    intent = self.openai_service.extract_search_intent(message, context)
                    
                    # Validate that the intent is valid
                    if self._validate_search_intent(intent):
                        logger.info(f"✅ Intent extracted successfully with OpenAI: {intent['type']}")
                        return intent
                    else:
                        logger.warning("⚠️ OpenAI intent invalid, using fallback")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Error with OpenAI, using fallback: {e}")
            
            # Fallback: use rule-based method
            logger.info("🔄 Using rule-based fallback method")
            return self._extract_search_intent_fallback(message, context)
                
        except Exception as e:
            logger.error(f"Error extracting search intent: {e}")
            return self._get_default_search_intent(message)
    
    def _extract_search_intent_fallback(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback method to extract intent based on rules"""
        try:
            message_lower = message.lower()
            
            # Detect query type using keywords
            if any(word in message_lower for word in ["comparar", "compare", "vs", "versus"]):
                return self._extract_compare_intent(message, context)
            elif any(word in message_lower for word in ["detalle", "details", "info", "información"]):
                return self._extract_detail_intent(message, context)
            elif any(word in message_lower for word in ["cerca", "near", "poi", "restaurantes", "escuelas", "schools"]):
                return self._extract_poi_intent(message, context)
            else:
                return self._extract_basic_search_intent(message, context)
                
        except Exception as e:
            logger.error(f"Error in fallback method: {e}")
            return self._get_default_search_intent(message)
    
    def _extract_basic_search_intent(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts basic search intent using simple rules"""
        # Basic rule-based fallback
        return {
            "type": "property_search",
            "query": message,
            "filters": {
                "city": context.get("city") if context else None,
                "property_id": context.get("propertyId") if context else None
            }
        }
    
    def _extract_detail_intent(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts property detail intent"""
        property_id = context.get("propertyId") if context else None
        
        # Try to extract ID from message if not in context
        if not property_id:
            # Look for patterns like "property 12345" or "house 18562768"
            match = re.search(r'\b(\d+)\b', message)
            if match:
                property_id = match.group(1)
        
        return {
            "type": "property_detail",
            "property_id": property_id,
            "query": message
        }
    
    def _extract_poi_intent(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts POI search intent"""
        property_id = context.get("propertyId") if context else None
        category = None
        radius = 1500
        
        # Detect category
        message_lower = message.lower()
        if any(word in message_lower for word in ["escuela", "school", "colegio"]):
            category = "school"
        elif any(word in message_lower for word in ["restaurante", "restaurant", "comida"]):
            category = "restaurant"
        elif any(word in message_lower for word in ["hospital", "clínica", "médico"]):
            category = "healthcare"
        elif any(word in message_lower for word in ["tienda", "shop", "comercio"]):
            category = "shopping"
        
        # Detect radius
        radius_match = re.search(r'(\d+)\s*(?:metros?|meters?|m)', message_lower)
        if radius_match:
            radius = int(radius_match.group(1))
        
        # If no property_id, change to property search near POIs
        if not property_id:
            return {
                "type": "property_search",
                "query": f"home near {category}" if category else message,
                "filters": {
                    "poi_category": category,
                    "poi_radius": radius
                },
                "search_mode": "near_pois"
            }
        else:
            return {
                "type": "poi_search",
                "property_id": property_id,
                "category": category,
                "radius": radius,
                "query": message
            }
    
    def _extract_compare_intent(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts property comparison intent"""
        # Search for IDs in message
        property_ids = re.findall(r'\b(\d{8,})\b', message)
        
        # If there is context, add propertyId
        if context and context.get("propertyId"):
            if context["propertyId"] not in property_ids:
                property_ids.insert(0, context["propertyId"])
        
        return {
            "type": "property_compare",
            "property_ids": property_ids[:5],  # Maximum 5 properties
            "query": message
        }
    
    def _validate_search_intent(self, intent: Dict[str, Any]) -> bool:
        """Validates that the extracted intent has the correct structure"""
        try:
            # Verify it's a dictionary
            if not isinstance(intent, dict):
                return False
            
            # Verify required keys
            required_keys = ["type", "query", "filters"]
            for key in required_keys:
                if key not in intent:
                    return False
            
            # Verify that the type is valid
            valid_types = ["property_search", "property_detail", "poi_search", "property_compare"]
            if intent["type"] not in valid_types:
                return False
            
            # Verify that query is not empty
            if not intent["query"] or not intent["query"].strip():
                return False
            
            # Verify that filters is a dictionary
            if not isinstance(intent["filters"], dict):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating intent: {e}")
            return False
    
    def _get_default_search_intent(self, message: str) -> Dict[str, Any]:
        """Returns a default search intent"""
        return {
            "type": "property_search",
            "query": message,
            "filters": {}
        }
