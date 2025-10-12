"""
Service for OpenAI intent extraction operations
Handles search intent extraction and analysis
"""
from typing import List, Dict, Any, Optional
import json
from .interfaces import OpenAIIntentExtractionInterface
from .connection_service import OpenAIConnectionService
from .chat_service import OpenAIChatService
import logging

logger = logging.getLogger(__name__)


class OpenAIIntentExtractionService(OpenAIIntentExtractionInterface):
    """Service for handling OpenAI intent extraction operations"""
    
    def __init__(self, connection_service: OpenAIConnectionService, chat_service: OpenAIChatService):
        self.connection_service = connection_service
        self.chat_service = chat_service
    
    def extract_search_intent(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts search intent from user message using OpenAI"""
        try:
            if not user_message or not user_message.strip():
                logger.warning("Empty message received for intent extraction")
                return self._get_default_search_intent("")
            
            logger.debug(f"Extracting intent for message: '{user_message[:50]}...'")
            
            # Build intent extraction prompt
            system_prompt = self._build_intent_prompt(user_message, context)
            
            # Build message with context
            full_message = user_message.strip()
            if context:
                context_str = json.dumps(context, ensure_ascii=False, indent=2)
                full_message += f"\n\nConversation context:\n{context_str}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_message}
            ]
            
            # Use chat service to generate response
            content = self.chat_service.generate_chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                temperature=0.2,
                max_tokens=600
            )
            
            logger.debug(f"Extracted intent response: {content}")
            
            # Parse JSON response
            try:
                # Clean possible extra characters before JSON
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                
                intent = json.loads(content.strip())
                
                # Validate and complete structure
                return self._validate_and_complete_intent(intent, user_message)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse JSON from intent: {e}")
                logger.warning(f"Received content: {content}")
                return self._get_default_search_intent(user_message)
            
        except Exception as e:
            logger.error(f"Error extracting search intent: {e}")
            return self._get_default_search_intent(user_message)
    
    def _build_intent_prompt(self, user_message: str, context: Optional[Dict[str, Any]]) -> str:
        """Builds the intent extraction prompt"""
        return """
        You are an assistant specialized in extracting Plotari property search information.
        Analyze the user's message and extract:
        1. Query type (search, detail, comparison, POIs)
        2. Location (city, state, neighborhood - only if explicitly mentioned)
        3. Features (bedrooms, bathrooms, area, price)
        4. Property type (house, condo, apartment, townhouse, etc.)
        5. Keywords for search
        
        IMPORTANT LOCATION RULES:
        - For the "state" field: only include if explicitly mentioned (e.g.: "in California", "CA", "Texas"). If not mentioned, use null.
        - For the "city" field: extract the name of the mentioned city (e.g.: "San Diego", "Los Angeles", "Miami")
        - For the "neighborhood" field: extract neighborhood/district names (e.g.: "Pacific Beach", "La Jolla", "Downtown", "Gaslamp Quarter")
        - CRITICAL: Distinguish between city and neighborhood. Common neighborhoods include: Pacific Beach, La Jolla, Downtown, Gaslamp Quarter, Little Italy, North Park, Hillcrest, Mission Valley, etc.
        - If only a neighborhood is mentioned without a city, use "neighborhood" field and leave "city" as null
        - If both city and neighborhood are mentioned, include both fields
        
        OTHER RULES:
        - Bedroom numbers: look for words like "habitaciones", "recamaras", "bedrooms", "hab", "bedroom", "bed"
        - Property type: look for words like "condo", "condos", "house", "houses", "apartment", "apartments", "townhouse", etc.
        - For comparisons: detect when multiple properties or IDs are mentioned
        - For details: detect when specific information about a property is requested
        - For POIs: detect when searching for restaurants, schools, hospitals, etc.
        
        CRITICAL RULES FOR PROPERTY SEARCHES NEAR POIs:
        - If user searches for "propiedades cerca de X" or "property near X", use type: "property_search" with search_mode: "near_pois"
        - If user searches for "what POIs are near property Y?", use type: "poi_search"
        - For property searches near POIs, include "search_mode": "near_pois" in filters
        
        Respond ONLY in valid JSON format with the following keys:
        - type: query type ("property_search", "property_detail", "poi_search", "property_compare")
        - query: optimized query for search
        - filters: object with specific filters (city, state, neighborhood, property_type, min_price, max_price, min_bedrooms, max_bedrooms, min_bathrooms, max_bathrooms, property_id, property_ids for comparison, poi_category, poi_radius, search_mode)
        
        Examples:
        User: "Looking for a 2 bedroom house in Crescent City"
        Response: {"type": "property_search", "query": "2 bedroom house Crescent City", "filters": {"city": "Crescent City", "state": null, "min_bedrooms": 2, "property_type": "House"}}
        
        User: "Do you have something in Pacific Beach"
        Response: {"type": "property_search", "query": "Pacific Beach", "filters": {"neighborhood": "Pacific Beach"}}
        
        User: "Show condos in La Jolla, San Diego"
        Response: {"type": "property_search", "query": "condos La Jolla San Diego", "filters": {"city": "San Diego", "neighborhood": "La Jolla", "property_type": "Condo"}}
        
        User: "Show condos between 200k and 300k"
        Response: {"type": "property_search", "query": "condos 200k-300k", "filters": {"property_type": "Condo", "min_price": 200000, "max_price": 300000}}
        
        User: "property near to parks" or "propiedades cerca de parques"
        Response: {"type": "property_search", "query": "property near parks", "filters": {"poi_category": "park", "poi_radius": 1500, "search_mode": "near_pois"}}
        
        User: "Compare properties 18562768 and 18562769"
        Response: {"type": "property_compare", "query": "compare properties", "filters": {"property_ids": ["18562768", "18562769"]}}
        
        User: "What restaurants are near property 18562768?"
        Response: {"type": "poi_search", "query": "restaurants near property", "filters": {"property_id": "18562768", "poi_category": "restaurant"}}
        """
    
    def _validate_and_complete_intent(self, intent: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Validates and completes the extracted intent structure"""
        try:
            # Ensure required keys exist
            if "type" not in intent:
                intent["type"] = "property_search"
            
            if "query" not in intent or not intent["query"]:
                intent["query"] = original_message
            
            if "filters" not in intent or not isinstance(intent["filters"], dict):
                intent["filters"] = {}
            
            # Validate type
            valid_types = ["property_search", "property_detail", "poi_search", "property_compare"]
            if intent["type"] not in valid_types:
                intent["type"] = "property_search"
            
            # Clean empty values in filters
            filters = intent.get("filters", {})
            cleaned_filters = {}
            for key, value in filters.items():
                if value is not None and value != "" and value != "null":
                    cleaned_filters[key] = value
            intent["filters"] = cleaned_filters
            
            logger.debug(f"Intent validated and completed: {intent}")
            return intent
            
        except Exception as e:
            logger.warning(f"Error validating intent: {e}")
            return self._get_default_search_intent(original_message)
    
    def _get_default_search_intent(self, user_message: str) -> Dict[str, Any]:
        """Returns a default search intent"""
        return {
            "type": "property_search",
            "query": user_message,
            "filters": {}
        }
