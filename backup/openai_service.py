"""
Service for interacting with OpenAI
Updated to work with new models
"""
import openai
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.models.property import Property, POI
import logging
import json
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for handling OpenAI operations"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        logger.info("OpenAIService initialized successfully")
    
    def generate_embeddings(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """Generates embeddings for given text"""
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            response = self.client.embeddings.create(
                input=text.strip(),
                model=model
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Embedding generated with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def generate_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generates chat response using OpenAI"""
        try:
            if not messages:
                raise ValueError("Message list cannot be empty")
            
            # Validate message structure
            for message in messages:
                if not isinstance(message, dict) or "role" not in message or "content" not in message:
                    raise ValueError("Each message must have 'role' and 'content'")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            logger.debug(f"Response generated with {len(content)} characters")
            return content
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise
    
    def extract_search_intent(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts search intent from user message using OpenAI"""
        try:
            if not user_message or not user_message.strip():
                logger.warning("Empty message received for intent extraction")
                return self._get_default_search_intent("")
            
            logger.debug(f"Extracting intent for message: '{user_message[:50]}...'")
            
            system_prompt = """
            You are an assistant specialized in extracting Plotari property search information.
            Analyze the user's message and extract:
            1. Query type (search, detail, comparison, POIs)
            2. Location (city, state - only if explicitly mentioned)
            3. Features (bedrooms, bathrooms, area, price)
            4. Keywords for search
            
            IMPORTANT:
            - For the "state" field: only include if explicitly mentioned (e.g.: "in California", "CA", "Texas"). If not mentioned, use null.
            - For the "city" field: extract the name of the mentioned city
            - If only a city is mentioned without state, leave state as null
            - Bedroom numbers: look for words like "habitaciones", "recámaras", "bedrooms", "hab", "bedroom", "bed"
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
            - filters: object with specific filters (city, state, min_price, max_price, min_bedrooms, max_bedrooms, min_bathrooms, max_bathrooms, property_id, property_ids for comparison, poi_category, poi_radius, search_mode)
            
            Examples:
            User: "Looking for a 2 bedroom house in Crescent City"
            Response: {"type": "property_search", "query": "2 bedroom house Crescent City", "filters": {"city": "Crescent City", "state": null, "min_bedrooms": 2}}
            
            User: "property near to parks" or "propiedades cerca de parques"
            Response: {"type": "property_search", "query": "property near parks", "filters": {"poi_category": "park", "poi_radius": 1500, "search_mode": "near_pois"}}
            
            User: "Compare properties 18562768 and 18562769"
            Response: {"type": "property_compare", "query": "compare properties", "filters": {"property_ids": ["18562768", "18562769"]}}
            
            User: "What restaurants are near property 18562768?"
            Response: {"type": "poi_search", "query": "restaurants near property", "filters": {"property_id": "18562768", "poi_category": "restaurant"}}
            """
            
            # Build message with context
            full_message = user_message.strip()
            if context:
                context_str = json.dumps(context, ensure_ascii=False, indent=2)
                full_message += f"\n\nConversation context:\n{context_str}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_message}
                ],
                temperature=0.2,  # Reduced for better consistency
                max_tokens=600,
                timeout=10  # 10 second timeout
            )
            
            content = response.choices[0].message.content.strip()
            logger.debug(f"Extracted intent response: {content}")
            
            # Intentar parsear JSON con mejor manejo de errores
            try:
                # Limpiar posibles caracteres extra antes del JSON
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                
                intent = json.loads(content.strip())
                
                # Validar y completar estructura
                return self._validate_and_complete_intent(intent, user_message)
                
            except json.JSONDecodeError as e:
                logger.warning(f"No se pudo parsear JSON de intención: {e}")
                logger.warning(f"Contenido recibido: {content}")
                return self._get_default_search_intent(user_message)
            
        except Exception as e:
            logger.error(f"Error extrayendo intención de búsqueda: {e}")
            return self._get_default_search_intent(user_message)
    
    def _validate_and_complete_intent(self, intent: Dict[str, Any], original_message: str) -> Dict[str, Any]:
        """Valida y completa la estructura de la intención extraída"""
        try:
            # Asegurar que tenga las claves necesarias
            if "type" not in intent:
                intent["type"] = "property_search"
            
            if "query" not in intent or not intent["query"]:
                intent["query"] = original_message
            
            if "filters" not in intent or not isinstance(intent["filters"], dict):
                intent["filters"] = {}
            
            # Validar tipo
            valid_types = ["property_search", "property_detail", "poi_search", "property_compare"]
            if intent["type"] not in valid_types:
                intent["type"] = "property_search"
            
            # Limpiar valores vacíos en filters
            filters = intent.get("filters", {})
            cleaned_filters = {}
            for key, value in filters.items():
                if value is not None and value != "" and value != "null":
                    cleaned_filters[key] = value
            intent["filters"] = cleaned_filters
            
            logger.debug(f"Intención validada y completada: {intent}")
            return intent
            
        except Exception as e:
            logger.warning(f"Error validando intención: {e}")
            return self._get_default_search_intent(original_message)
    
    def _get_default_search_intent(self, user_message: str) -> Dict[str, Any]:
        """Returns a default search intent"""
        return {
            "type": "property_search",
            "query": user_message,
            "filters": {}
        }
    
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
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
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
    
    def is_available(self) -> bool:
        """Checks if OpenAI service is available"""
        try:
            # Make a simple call to verify connection
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI not available: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Returns list of available models"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data if 'gpt' in model.id or 'embedding' in model.id]
        except Exception as e:
            logger.error(f"Error obteniendo modelos: {e}")
            return []
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # OpenAI client no necesita cierre explícito
        pass