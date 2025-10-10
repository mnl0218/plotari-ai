"""
Main chatbot service
Updated to work with new models
"""
from typing import List, Dict, Any, Optional
from src.services.weaviate_service import WeaviateService
from src.services.openai_service import OpenAIService
from src.utils.json_cache import JSONCacheManager
from src.models.property import (
    ChatRequest, ChatResponse, PropertySearchRequest, 
    Property, POI, PropertySearchResponse, POISearchRequest, POISearchResponse
)
import logging
import uuid
import os
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ChatbotService:
    """Main Plotari chatbot service"""
    
    def __init__(self, cache_dir: str = "cache/conversations", cache_max_age_hours: int = 24):
        self.weaviate_service = None
        self.openai_service = None
        # JSON cache instead of memory
        self.json_cache = JSONCacheManager(cache_dir, cache_max_age_hours)
        # Keep cache in memory for fast access (optional)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_max_size = 100  # Maximum conversations in memory
        self._initialize_services()
    
    def _initialize_services(self) -> None:
        """Initializes necessary services"""
        try:
            self.weaviate_service = WeaviateService()
            self.openai_service = OpenAIService()
            logger.info("ChatbotService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            raise
    
    def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Processes a user message and generates a response
        Detects intent → routes to /search, /pois, /property internally and composes response in natural language
        """
        try:
            # Validate input
            if not request.message or not request.message.strip():
                return self._create_error_response(
                    "Please provide a valid message."
                )
            
            # Get or create conversation session
            session_id = request.session_id
            conversation = self._get_or_create_conversation(session_id)
            
            # Add user message to history
            conversation["messages"].append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Extract search intent with conversation context
            search_intent = self._extract_search_intent(
                request.message, 
                self._build_context_from_conversation(conversation)
            )
            logger.info(f"Search intent extracted: {search_intent}")
            
            # Process according to detected intent
            properties_found = []
            pois_found = []
            
            if search_intent["type"] == "property_search":
                properties_found = self._search_properties(search_intent)
            elif search_intent["type"] == "property_detail":
                property_detail = self._get_property_detail(search_intent)
                if property_detail:
                    properties_found = [property_detail.property]
            elif search_intent["type"] == "poi_search":
                pois_found = self._search_pois(search_intent)
            elif search_intent["type"] == "property_compare":
                properties_found = self._compare_properties(search_intent)
            
            # Generate contextual response with history
            response_text = self._generate_response(
                request.message, 
                properties_found, 
                pois_found, 
                search_intent,
                conversation
            )
            
            # Add assistant response to history
            assistant_message = {
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat(),
                "search_intent": search_intent,
                "properties_found": len(properties_found),
                "pois_found": len(pois_found)
            }
            
            # Include complete properties if any
            if properties_found:
                assistant_message["properties"] = [prop.model_dump() for prop in properties_found]
                logger.info(f"🏠 Saving {len(properties_found)} complete properties in message")
            
            # Include complete POIs if any
            if pois_found:
                assistant_message["pois"] = [poi.model_dump() for poi in pois_found]
                logger.info(f"📍 Saving {len(pois_found)} complete POIs in message")
            
            conversation["messages"].append(assistant_message)
            
            # Update conversation context
            self._update_conversation_context(conversation, search_intent, properties_found)
            
            # Save conversation to JSON cache
            self._save_conversation_to_cache(session_id, conversation)
            
            # Clean up old conversations
            self._cleanup_old_conversations()
            
            # Create response
            response = ChatResponse(
                message=response_text,
                properties_found=properties_found[:5] if properties_found else None,
                pois_found=pois_found[:5] if pois_found else None,
                metadata={
                    "search_intent": search_intent,
                    "total_properties_found": len(properties_found),
                    "total_pois_found": len(pois_found),
                    "session_id": session_id,
                    "conversation_length": len(conversation["messages"])
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(
                "Sorry, an error occurred while processing your query. Please try again.",
                str(e)
            )
    
    def _extract_search_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
    
    def _get_or_create_conversation(self, session_id: str) -> Dict[str, Any]:
        """Obtiene o crea una conversación para la sesión usando cache JSON"""
        # Primero verificar cache en memoria
        if session_id in self._memory_cache:
            conversation = self._memory_cache[session_id]
            conversation["last_activity"] = datetime.now().isoformat()
            return conversation
        
        # Intentar cargar desde cache JSON
        conversation = self.json_cache.load_conversation(session_id)
        
        if conversation is None:
            # Crear nueva conversación
            conversation = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "messages": [],
                "context": {
                    "last_search_intent": None,
                    "last_properties": [],
                    "last_pois": [],
                    "user_preferences": {},
                    "current_location": None,
                    "current_property": None
                }
            }
            logger.info(f"Nueva conversación creada: {session_id}")
        else:
            # Actualizar última actividad
            conversation["last_activity"] = datetime.now().isoformat()
            logger.debug(f"Conversación cargada desde cache: {session_id}")
        
        # Agregar a cache en memoria (con límite)
        self._add_to_memory_cache(session_id, conversation)
        
        return conversation
    
    def _add_to_memory_cache(self, session_id: str, conversation: Dict[str, Any]) -> None:
        """Agrega conversación al cache en memoria con límite de tamaño"""
        # Si el cache está lleno, eliminar la conversación más antigua
        if len(self._memory_cache) >= self._cache_max_size:
            oldest_session = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k].get("last_activity", "")
            )
            del self._memory_cache[oldest_session]
        
        self._memory_cache[session_id] = conversation
    
    def _save_conversation_to_cache(self, session_id: str, conversation: Dict[str, Any]) -> None:
        """Guarda conversación en cache JSON"""
        try:
            success = self.json_cache.save_conversation(session_id, conversation)
            if not success:
                logger.warning(f"Could not save conversation {session_id} to JSON cache")
        except Exception as e:
            logger.error(f"Error saving conversation {session_id}: {e}")
    
    def _build_context_from_conversation(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Construye contexto a partir de la conversación"""
        context = conversation.get("context", {})
        
        # Agregar información del último mensaje si es relevante
        messages = conversation.get("messages", [])
        if messages:
            last_message = messages[-1]
            if last_message.get("role") == "user":
                # Extraer información del último mensaje del usuario
                content = last_message.get("content", "").lower()
                
                # Detectar ubicación mencionada
                if any(word in content for word in ["crescent city", "california", "ca"]):
                    context["current_location"] = "Crescent City, CA"
                
                # Detectar tipo de propiedad mencionada
                if any(word in content for word in ["casa", "house", "home"]):
                    context["user_preferences"]["property_type"] = "house"
                elif any(word in content for word in ["apartamento", "apartment", "condo"]):
                    context["user_preferences"]["property_type"] = "apartment"
        
        return context
    
    def _update_conversation_context(self, conversation: Dict[str, Any], search_intent: Dict[str, Any], properties_found: List[Property]) -> None:
        """Actualiza el contexto de la conversación"""
        context = conversation.get("context", {})
        
        # Actualizar última intención de búsqueda
        context["last_search_intent"] = search_intent
        
        # Actualizar últimas propiedades encontradas
        if properties_found:
            context["last_properties"] = [
                {
                    "zpid": prop.zpid,
                    "address": prop.address,
                    "price": prop.price,
                    "city": prop.city
                }
                for prop in properties_found[:3]  # Solo las primeras 3
            ]
        
        # Actualizar preferencias del usuario basadas en búsquedas
        filters = search_intent.get("filters", {})
        if filters.get("city"):
            context["user_preferences"]["preferred_city"] = filters["city"]
        if filters.get("min_bedrooms"):
            context["user_preferences"]["min_bedrooms"] = filters["min_bedrooms"]
        if filters.get("max_price"):
            context["user_preferences"]["max_price"] = filters["max_price"]
    
    def _cleanup_old_conversations(self) -> None:
        """Limpia conversaciones antiguas usando cache JSON"""
        try:
            # Limpiar cache JSON
            deleted_count = self.json_cache.cleanup_expired_conversations()
            
            # Limpiar cache en memoria basado en tiempo
            cutoff_time = datetime.now() - timedelta(hours=1)
            sessions_to_remove = []
            
            for session_id, conversation in self._memory_cache.items():
                try:
                    last_activity = datetime.fromisoformat(conversation.get("last_activity", ""))
                    if last_activity < cutoff_time:
                        sessions_to_remove.append(session_id)
                except (ValueError, TypeError):
                    # Si hay error parseando la fecha, eliminar
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self._memory_cache[session_id]
                logger.debug(f"Conversación {session_id} eliminada del cache en memoria")
            
            if deleted_count > 0 or sessions_to_remove:
                logger.info(f"Limpieza completada: {deleted_count} archivos JSON, {len(sessions_to_remove)} cache memoria")
                
        except Exception as e:
            logger.error(f"Error in conversation cleanup: {e}")
    
    def _validate_search_intent(self, intent: Dict[str, Any]) -> bool:
        """Valida que la intención extraída tenga la estructura correcta"""
        try:
            # Verificar que sea un diccionario
            if not isinstance(intent, dict):
                return False
            
            # Verificar claves requeridas
            required_keys = ["type", "query", "filters"]
            for key in required_keys:
                if key not in intent:
                    return False
            
            # Verificar que el tipo sea válido
            valid_types = ["property_search", "property_detail", "poi_search", "property_compare"]
            if intent["type"] not in valid_types:
                return False
            
            # Verificar que query no esté vacío
            if not intent["query"] or not intent["query"].strip():
                return False
            
            # Verificar que filters sea un diccionario
            if not isinstance(intent["filters"], dict):
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error validating intent: {e}")
            return False
    
    def _extract_search_intent_fallback(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Método de fallback para extraer intención basado en reglas"""
        try:
            message_lower = message.lower()
            
            # Detectar tipo de consulta usando palabras clave
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
        """Extrae intención de búsqueda básica usando reglas simples"""
        # Fallback básico basado en reglas
        return {
            "type": "property_search",
            "query": message,
            "filters": {
                "city": context.get("city") if context else None,
                "property_id": context.get("propertyId") if context else None
            }
        }
    
    def _extract_detail_intent(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrae intención de detalle de propiedad"""
        property_id = context.get("propertyId") if context else None
        
        # Intentar extraer ID del mensaje si no está en contexto
        if not property_id:
            # Buscar patrones como "propiedad 12345" o "casa 18562768"
            import re
            match = re.search(r'\b(\d+)\b', message)
            if match:
                property_id = match.group(1)
        
        return {
            "type": "property_detail",
            "property_id": property_id,
            "query": message
        }
    
    def _extract_poi_intent(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extrae intención de búsqueda de POIs"""
        property_id = context.get("propertyId") if context else None
        category = None
        radius = 1500
        
        # Detectar categoría
        message_lower = message.lower()
        if any(word in message_lower for word in ["escuela", "school", "colegio"]):
            category = "school"
        elif any(word in message_lower for word in ["restaurante", "restaurant", "comida"]):
            category = "restaurant"
        elif any(word in message_lower for word in ["hospital", "clínica", "médico"]):
            category = "healthcare"
        elif any(word in message_lower for word in ["tienda", "shop", "comercio"]):
            category = "shopping"
        
        # Detectar radio
        import re
        radius_match = re.search(r'(\d+)\s*(?:metros?|meters?|m)', message_lower)
        if radius_match:
            radius = int(radius_match.group(1))
        
        # Si no hay property_id, cambiar a búsqueda de propiedades cerca de POIs
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
        """Extrae intención de comparación de propiedades"""
        # Buscar IDs en el mensaje
        import re
        property_ids = re.findall(r'\b(\d{8,})\b', message)
        
        # Si hay contexto, agregar propertyId
        if context and context.get("propertyId"):
            if context["propertyId"] not in property_ids:
                property_ids.insert(0, context["propertyId"])
        
        return {
            "type": "property_compare",
            "property_ids": property_ids[:5],  # Máximo 5 propiedades
            "query": message
        }
    
    def _search_properties(self, search_intent: Dict[str, Any]) -> List[Property]:
        """Busca propiedades basándose en la intención de búsqueda"""
        try:
            if not search_intent.get("query") or not self.weaviate_service:
                return []
            
            # Modo especial: buscar propiedades cerca de POIs
            if search_intent.get("search_mode") == "near_pois":
                return self._search_properties_near_pois(search_intent)
            
            # Construir request de búsqueda con valores limpios
            filters = search_intent.get("filters", {})
            
            # Función helper para limpiar valores string vacíos
            def clean_value(value):
                if isinstance(value, str) and not value.strip():
                    return None
                return value
            
            search_request = PropertySearchRequest(
                query=search_intent["query"],
                limit=10,
                city=clean_value(filters.get("city")),
                state=clean_value(filters.get("state")),
                property_type=clean_value(filters.get("property_type")),
                min_price=filters.get("min_price"),
                max_price=filters.get("max_price"),
                min_bedrooms=filters.get("min_bedrooms"),
                max_bedrooms=filters.get("max_bedrooms"),
                min_bathrooms=filters.get("min_bathrooms"),
                max_bathrooms=filters.get("max_bathrooms"),
                latitude=filters.get("latitude"),
                longitude=filters.get("longitude"),
                radius=filters.get("radius")
            )
            
            search_response = self.weaviate_service.search_properties(search_request)
            return search_response.properties
            
        except Exception as e:
            logger.error(f"Error searching properties: {e}")
            return []
    
    def _search_properties_near_pois(self, search_intent: Dict[str, Any]) -> List[Property]:
        """Busca propiedades cerca de POIs específicos"""
        try:
            filters = search_intent.get("filters", {})
            poi_category = filters.get("poi_category")
            poi_radius = filters.get("poi_radius", 2000)  # Radio por defecto más amplio
            
            if not self.weaviate_service:
                return []
            
            # Primero buscar todos los POIs de la categoría especificada
            pois = self.weaviate_service._get_pois_by_category(poi_category)
            
            if not pois:
                logger.info(f"No POIs found for category: {poi_category}")
                return []
            
            # Buscar propiedades cerca de cada POI
            all_properties = []
            for poi in pois:
                if hasattr(poi.geo, 'latitude') and hasattr(poi.geo, 'longitude'):
                    # Buscar propiedades en un radio del POI
                    search_request = PropertySearchRequest(
                        query=search_intent["query"],
                        latitude=poi.geo.latitude,
                        longitude=poi.geo.longitude,
                        radius=poi_radius,
                        limit=5  # Máximo 5 por POI
                    )
                    
                    search_response = self.weaviate_service.search_properties(search_request)
                    all_properties.extend(search_response.properties)
            
            # Eliminar duplicados y limitar resultados
            unique_properties = []
            seen_zpids = set()
            for prop in all_properties:
                if prop.zpid not in seen_zpids:
                    unique_properties.append(prop)
                    seen_zpids.add(prop.zpid)
                    if len(unique_properties) >= 10:  # Máximo 10 propiedades
                        break
            
            return unique_properties
            
        except Exception as e:
            logger.error(f"Error searching properties near POIs: {e}")
            return []
    
    def _get_property_detail(self, search_intent: Dict[str, Any]) -> Optional[Any]:
        """Obtiene detalle de una propiedad"""
        try:
            property_id = search_intent.get("property_id")
            if not property_id or not self.weaviate_service:
                return None
            
            return self.weaviate_service.get_property_detail(property_id)
            
        except Exception as e:
            logger.error(f"Error getting property detail: {e}")
            return None
    
    def _search_pois(self, search_intent: Dict[str, Any]) -> List[POI]:
        """Busca POIs basándose en la intención"""
        try:
            property_id = search_intent.get("property_id")
            if not property_id or not self.weaviate_service:
                return []
            
            poi_request = POISearchRequest(
                property_id=property_id,
                category=search_intent.get("category"),
                radius=search_intent.get("radius", 1500),
                limit=10
            )
            
            poi_response = self.weaviate_service.search_pois(poi_request)
            return poi_response.pois
            
        except Exception as e:
            logger.error(f"Error searching POIs: {e}")
            return []
    
    def _compare_properties(self, search_intent: Dict[str, Any]) -> List[Property]:
        """Compara propiedades basándose en la intención"""
        try:
            property_ids = search_intent.get("property_ids", [])
            if len(property_ids) < 2 or not self.weaviate_service:
                return []
            
            from src.models.property import PropertyCompareRequest
            compare_request = PropertyCompareRequest(property_ids=property_ids)
            compare_response = self.weaviate_service.compare_properties(compare_request)
            return compare_response.properties
            
        except Exception as e:
            logger.error(f"Error comparing properties: {e}")
            return []
    
    def _generate_response(self, message: str, properties: List[Property], pois: List[POI], search_intent: Dict[str, Any], conversation: Optional[Dict[str, Any]] = None) -> str:
        """Genera una respuesta contextual"""
        try:
            if self.openai_service:
                # Incluir contexto de conversación si está disponible
                context_info = ""
                if conversation:
                    context = conversation.get("context", {})
                    user_preferences = context.get("user_preferences", {})
                    
                    if user_preferences:
                        context_info = f"\nContexto de conversación:\n"
                        if user_preferences.get("preferred_city"):
                            context_info += f"- Ciudad preferida: {user_preferences['preferred_city']}\n"
                        if user_preferences.get("property_type"):
                            context_info += f"- Tipo de propiedad: {user_preferences['property_type']}\n"
                        if user_preferences.get("min_bedrooms"):
                            context_info += f"- Mínimo habitaciones: {user_preferences['min_bedrooms']}\n"
                        if user_preferences.get("max_price"):
                            context_info += f"- Precio máximo: ${user_preferences['max_price']:,}\n"
                    
                    # Agregar historial reciente si hay mensajes previos
                    messages = conversation.get("messages", [])
                    if len(messages) > 1:
                        context_info += f"\nConversación previa ({len(messages)-1} mensajes):\n"
                        for msg in messages[-3:-1]:  # Últimos 2 mensajes antes del actual
                            role = "Usuario" if msg.get("role") == "user" else "Asistente"
                            context_info += f"- {role}: {msg.get('content', '')[:100]}...\n"
                
                enhanced_message = message + context_info
                return self.openai_service.generate_property_response(enhanced_message, properties, pois, search_intent)
            else:
                return self._get_fallback_response(properties, pois, search_intent)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(properties, pois, search_intent)
    
    def _get_fallback_response(self, properties: List[Property], pois: List[POI], search_intent: Dict[str, Any]) -> str:
        """Retorna una respuesta de fallback"""
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
    
    def _get_default_search_intent(self, message: str) -> Dict[str, Any]:
        """Retorna una intención de búsqueda por defecto"""
        return {
            "type": "property_search",
            "query": message,
            "filters": {}
        }
    
    def _create_error_response(self, message: str, error: Optional[str] = None) -> ChatResponse:
        """Crea una respuesta de error"""
        return ChatResponse(
            message=message,
            metadata={"error": error} if error else {}
        )
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene el historial de conversación para una sesión con propiedades enriquecidas"""
        # Primero verificar cache en memoria
        if session_id in self._memory_cache:
            conversation = self._memory_cache[session_id]
            messages = conversation.get("messages", [])
            enriched_messages = self._enrich_messages_with_properties(messages, conversation)
            return enriched_messages[-limit:] if limit else enriched_messages
        
        # Cargar desde cache JSON
        conversation = self.json_cache.load_conversation(session_id)
        if conversation is None:
            return []
        
        messages = conversation.get("messages", [])
        enriched_messages = self._enrich_messages_with_properties(messages, conversation)
        return enriched_messages[-limit:] if limit else enriched_messages
    
    def _enrich_messages_with_properties(self, messages: List[Dict[str, Any]], conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Los mensajes ya incluyen las propiedades completas desde la nueva implementación"""
        # Los mensajes ya vienen enriquecidos desde process_message, solo devolver tal como están
        logger.info(f"📚 Devolviendo {len(messages)} mensajes (ya enriquecidos)")
        return messages
    
    def clear_conversation(self, session_id: str) -> bool:
        """Limpia una conversación específica"""
        success = False
        
        # Eliminar del cache en memoria
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]
            success = True
        
        # Eliminar del cache JSON
        if self.json_cache.delete_conversation(session_id):
            success = True
        
        return success
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Obtiene información detallada del cache"""
        return {
            "json_cache": self.json_cache.get_cache_stats(),
            "memory_cache": {
                "conversations": len(self._memory_cache),
                "max_size": self._cache_max_size,
                "usage_percentage": (len(self._memory_cache) / self._cache_max_size) * 100
            },
            "conversations_list": self.json_cache.list_conversations()
        }
    
    def clear_all_cache(self) -> Dict[str, Any]:
        """Limpia todo el cache (memoria y JSON)"""
        # Limpiar cache en memoria
        memory_cleared = len(self._memory_cache)
        self._memory_cache.clear()
        
        # Limpiar cache JSON
        json_cleared = self.json_cache.clear_all_cache()
        
        return {
            "memory_conversations_cleared": memory_cleared,
            "json_files_cleared": json_cleared,
            "total_cleared": memory_cleared + json_cleared
        }
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de las conversaciones"""
        # Estadísticas del cache JSON
        json_stats = self.json_cache.get_cache_stats()
        
        # Estadísticas del cache en memoria
        memory_conversations = len(self._memory_cache)
        memory_messages = sum(len(conv.get("messages", [])) for conv in self._memory_cache.values())
        
        return {
            "total_conversations": json_stats.get("total_conversations", 0),
            "total_messages": json_stats.get("total_messages", 0),
            "active_sessions": json_stats.get("total_conversations", 0),
            "memory_cache_conversations": memory_conversations,
            "memory_cache_messages": memory_messages,
            "json_cache_size_mb": json_stats.get("total_size_mb", 0),
            "memory_usage_mb": len(str(self._memory_cache)) / 1024 / 1024,
            "cache_directory": json_stats.get("cache_directory", ""),
            "oldest_conversation": json_stats.get("oldest_conversation"),
            "newest_conversation": json_stats.get("newest_conversation")
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Obtiene el estado de los servicios"""
        status = {
            "weaviate_available": False,
            "openai_available": False,
            "conversations": self.get_conversation_stats()
        }
        
        try:
            if self.weaviate_service:
                status["weaviate_available"] = self.weaviate_service.is_connected()
        except Exception as e:
            logger.warning(f"Error checking Weaviate: {e}")
        
        try:
            if self.openai_service:
                status["openai_available"] = self.openai_service.is_available()
        except Exception as e:
            logger.warning(f"Error checking OpenAI: {e}")
        
        return status
    
    def close(self) -> None:
        """Cierra las conexiones"""
        try:
            if self.weaviate_service:
                self.weaviate_service.close()
            logger.info("ChatbotService cerrado correctamente")
        except Exception as e:
            logger.error(f"Error closing ChatbotService: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()