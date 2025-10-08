"""
Service for contextual response generation
Handles response generation using OpenAI and rule-based fallback
"""
from typing import List, Dict, Any, Optional
from .interfaces import ResponseGeneratorInterface
from src.services.openai import OpenAIService
from src.models.property import Property, POI
import logging

logger = logging.getLogger(__name__)


class ResponseGeneratorService(ResponseGeneratorInterface):
    """Service for contextual response generation"""
    
    def __init__(self, openai_service: Optional[OpenAIService] = None):
        self.openai_service = openai_service
    
    def generate_response(self, message: str, properties: List[Property], pois: List[POI], 
                         search_intent: Dict[str, Any], conversation: Optional[Dict[str, Any]] = None) -> str:
        """Generates a contextual response"""
        try:
            if self.openai_service:
                # Include conversation context if available
                context_info = ""
                if conversation:
                    context = conversation.get("context", {})
                    user_preferences = context.get("user_preferences", {})
                    
                    if user_preferences:
                        context_info = f"\nConversation context:\n"
                        if user_preferences.get("preferred_city"):
                            context_info += f"- Preferred city: {user_preferences['preferred_city']}\n"
                        if user_preferences.get("property_type"):
                            context_info += f"- Property type: {user_preferences['property_type']}\n"
                        if user_preferences.get("min_bedrooms"):
                            context_info += f"- Minimum bedrooms: {user_preferences['min_bedrooms']}\n"
                        if user_preferences.get("max_price"):
                            context_info += f"- Maximum price: ${user_preferences['max_price']:,}\n"
                    
                    # Add recent history if there are previous messages
                    messages = conversation.get("messages", [])
                    if len(messages) > 1:
                        context_info += f"\nPrevious conversation ({len(messages)-1} messages):\n"
                        for msg in messages[-3:-1]:  # Last 2 messages before current
                            role = "User" if msg.get("role") == "user" else "Assistant"
                            context_info += f"- {role}: {msg.get('content', '')[:100]}...\n"
                
                enhanced_message = message + context_info
                return self.openai_service.generate_property_response(enhanced_message, properties, pois, search_intent)
            else:
                return self._get_fallback_response(properties, pois, search_intent)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(properties, pois, search_intent)
    
    def _get_fallback_response(self, properties: List[Property], pois: List[POI], search_intent: Dict[str, Any]) -> str:
        """Returns a fallback response"""
        intent_type = search_intent.get("type", "property_search")
        
        if intent_type == "property_search":
            if properties:
                return f"I found {len(properties)} properties that match your search. Would you like to see more details about any particular one?"
            else:
                return "I didn't find any properties that match your search. Could you be more specific about what you're looking for?"
        
        elif intent_type == "property_detail":
            if properties:
                prop = properties[0]
                return f"Here's information about {prop.address} in {prop.city}. Price: ${prop.price:,}, {prop.bedrooms} bedrooms, {prop.bathrooms} bathrooms."
            else:
                return "I couldn't find detailed information about that property. Could you provide the property ID?"
        
        elif intent_type == "poi_search":
            if pois:
                return f"I found {len(pois)} points of interest near the property. Would you like to see more details?"
            else:
                return "I didn't find any points of interest near that location. Could you specify a larger radius?"
        
        elif intent_type == "property_compare":
            if properties:
                return f"I compared {len(properties)} properties. Would you like to see a detailed comparison table?"
            else:
                return "I couldn't find the properties to compare. Could you provide the property IDs?"
        
        return "I understand your query, but I need more information to help you better."
