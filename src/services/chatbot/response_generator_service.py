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
            # Handle general conversation separately
            if search_intent.get("type") == "general_conversation":
                if self.openai_service:
                    return self._generate_conversational_response(message, conversation)
                else:
                    return self._get_fallback_conversational_response(message)
            
            # Handle property-related intents
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
    
    def _generate_conversational_response(self, message: str, conversation: Optional[Dict[str, Any]] = None) -> str:
        """Generates a natural conversational response using OpenAI"""
        try:
            # Build conversation history for context
            conversation_history = []
            if conversation:
                messages = conversation.get("messages", [])
                # Include last 5 messages for context
                for msg in messages[-5:]:
                    if msg.get("role") in ["user", "assistant"]:
                        conversation_history.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
            
            system_prompt = """
            You are Plotari, a friendly and helpful AI real estate assistant.
            
            Your personality:
            - Warm, professional, and conversational
            - Eager to help users find their perfect property
            - Knowledgeable about real estate
            
            Your capabilities:
            - Search for properties by location, price, bedrooms, bathrooms, and features
            - Provide detailed information about specific properties
            - Find nearby points of interest (restaurants, schools, parks, etc.)
            - Compare multiple properties
            - Answer general questions about real estate
            
            Guidelines:
            - When greeting users, be warm and welcoming
            - When asked about capabilities, explain what you can do
            - When thanked, respond graciously and offer continued help
            - Keep responses concise but friendly
            - If appropriate, gently guide the conversation towards helping them find properties
            - Respond in English
            """
            
            # Build messages for OpenAI
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": message})
            
            # Generate response using OpenAI
            response = self.openai_service.generate_chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                temperature=0.8,
                max_tokens=300
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating conversational response: {e}")
            return self._get_fallback_conversational_response(message)
    
    def _get_fallback_conversational_response(self, message: str) -> str:
        """Returns a fallback conversational response when OpenAI is not available"""
        message_lower = message.lower().strip()
        
        # Greetings
        if any(greeting in message_lower for greeting in ["hello", "hi", "hey", "hola", "good morning", "good afternoon", "good evening", "buenos días", "buenas tardes"]):
            return "Hello! Welcome to Plotari. I'm here to help you find your perfect property. What are you looking for today?"
        
        # What can you do / help
        if any(phrase in message_lower for phrase in ["what can you", "how can you help", "what do you do", "help me", "qué puedes", "cómo puedes ayudar"]):
            return "I can help you find properties! Just tell me what you're looking for - like location, number of bedrooms, price range, or any specific features. I can also show you nearby restaurants, schools, parks, and compare different properties. What interests you?"
        
        # Thank you
        if any(phrase in message_lower for phrase in ["thank", "thanks", "gracias", "appreciate"]):
            return "You're welcome! If you need help finding properties or have any questions, I'm here to assist. Just let me know!"
        
        # Goodbye
        if any(phrase in message_lower for phrase in ["bye", "goodbye", "see you", "adiós", "hasta luego"]):
            return "Goodbye! Feel free to come back anytime you need help finding properties. Have a great day!"
        
        # How are you
        if any(phrase in message_lower for phrase in ["how are you", "cómo estás"]):
            return "I'm doing great, thank you! Ready to help you find the perfect property. What are you looking for?"
        
        # Default
        return "I'm here to help you find properties! You can ask me about houses, condos, or apartments in specific locations, or tell me your preferences like price range, number of bedrooms, etc. What would you like to know?"
