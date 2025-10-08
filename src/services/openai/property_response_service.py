"""
Service for OpenAI property response generation
Handles contextual response generation for properties and POIs
"""
from typing import List, Dict, Any, Optional
from src.models.property import Property, POI
from .interfaces import OpenAIPropertyResponseInterface
from .connection_service import OpenAIConnectionService
from .chat_service import OpenAIChatService
import logging

logger = logging.getLogger(__name__)


class OpenAIPropertyResponseService(OpenAIPropertyResponseInterface):
    """Service for handling OpenAI property response generation"""
    
    def __init__(self, connection_service: OpenAIConnectionService, chat_service: OpenAIChatService):
        self.connection_service = connection_service
        self.chat_service = chat_service
    
    def generate_property_response(
        self, 
        user_message: str, 
        properties: List[Property], 
        pois: List[POI] = None,
        search_intent: Dict[str, Any] = None
    ) -> str:
        """Generates a contextual response about found properties"""
        try:
            if not user_message or not user_message.strip():
                return "Please provide more details about what you're looking for."
            
            system_prompt = """
            You are an expert Plotari assistant. Respond naturally and helpfully about the properties and POIs found.
            Include relevant information such as price, location, main features.
            If there are no results, explain why and suggest alternatives.
            Maintain a professional but friendly tone.
            Respond in English.
            """
            
            # Prepare context with properties and POIs
            context = self._build_response_context(properties, pois, search_intent)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {user_message.strip()}\n\n{context}"}
            ]
            
            # Use chat service to generate response
            content = self.chat_service.generate_chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=800
            )
            
            logger.debug(f"Response generated: {len(content)} characters")
            return content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(properties, pois, search_intent)
    
    def _build_response_context(
        self, 
        properties: List[Property], 
        pois: List[POI] = None, 
        search_intent: Dict[str, Any] = None
    ) -> str:
        """Builds context of properties and POIs for response"""
        context = ""
        
        # Information about query type
        if search_intent:
            context += f"Query type: {search_intent.get('type', 'property_search')}\n"
        
        # Properties found
        if properties:
            context += f"\nProperties found: {len(properties)} results\n\n"
            
            for i, prop in enumerate(properties[:5], 1):  # Show maximum 5 properties
                context += f"{i}. {prop.address}, {prop.city}, {prop.state}\n"
                context += f"   Price: ${prop.price:,.0f}\n" if prop.price else "   Price: Not available\n"
                context += f"   {prop.bedrooms} bed, {prop.bathrooms} bath" if prop.bedrooms and prop.bathrooms else "   Bedrooms: Not specified"
                if prop.living_area:
                    context += f", {prop.living_area:,.0f} sqft"
                context += "\n"
                if prop.description:
                    context += f"   Description: {prop.description[:100]}...\n"
                context += "\n"
        else:
            context += "No properties found matching the search.\n"
        
        # POIs found
        if pois:
            context += f"\nPoints of interest found: {len(pois)} results\n\n"
            
            for i, poi in enumerate(pois[:5], 1):  # Show maximum 5 POIs
                context += f"{i}. {poi.name}\n"
                context += f"   Category: {poi.category}\n"
                if poi.rating:
                    context += f"   Rating: {poi.rating}/5\n"
                context += "\n"
        
        return context
    
    def _get_fallback_response(
        self, 
        properties: List[Property], 
        pois: List[POI] = None, 
        search_intent: Dict[str, Any] = None
    ) -> str:
        """Returns a fallback response when there are errors"""
        intent_type = search_intent.get("type", "property_search") if search_intent else "property_search"
        
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
