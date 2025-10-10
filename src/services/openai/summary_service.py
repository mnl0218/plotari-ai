"""
Service for OpenAI chat summary generation
Handles conversation summary generation using OpenAI
"""
from typing import List, Dict, Any, Optional
from .interfaces import OpenAIChatInterface
from .connection_service import OpenAIConnectionService
import logging

logger = logging.getLogger(__name__)


class OpenAISummaryService:
    """Service for handling OpenAI chat summary generation"""
    
    def __init__(self, connection_service: OpenAIConnectionService, chat_service: OpenAIChatInterface):
        self.connection_service = connection_service
        self.chat_service = chat_service
    
    def generate_chat_summary(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a summary of the user's first message and context
        
        Args:
            user_message: The first user message in the conversation
            context: Optional conversation context
            
        Returns:
            Generated summary string
        """
        try:
            if not user_message or not user_message.strip():
                logger.warning("Empty message received for summary generation")
                return "User started a conversation"
            
            logger.debug(f"Generating summary for message: '{user_message[:50]}...'")
            
            # Build summary generation prompt
            system_prompt = self._build_summary_prompt()
            
            # Prepare the message with context
            full_message = user_message.strip()
            if context:
                context_str = self._format_context_for_summary(context)
                if context_str:
                    full_message += f"\n\nContext: {context_str}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_message}
            ]
            
            # Use chat service to generate summary
            summary = self.chat_service.generate_chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",
                temperature=0.3,  # Lower temperature for more consistent summaries
                max_tokens=200    # Shorter summaries
            )
            
            logger.debug(f"Generated summary: {summary}")
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating chat summary: {e}")
            # Return a fallback summary based on the message
            return self._generate_fallback_summary(user_message)
    
    def _build_summary_prompt(self) -> str:
        """Builds the system prompt for summary generation"""
        return """
            You are an expert at creating concise, informative summaries of Plotari conversations.

            Your task is to create a brief summary (1-2 sentences) of what the user is looking for in their Plotari search.

            Focus on:
            - Property type (house, apartment, condo, etc.)
            - Location preferences (city, neighborhood, area)
            - Key requirements (bedrooms, bathrooms, price range, features)
            - Any specific needs or preferences mentioned

            Keep the summary professional, clear, and under 100 words.
            Write in English.
            """
    
    def _format_context_for_summary(self, context: Dict[str, Any]) -> str:
        """Formats conversation context for summary generation"""
        context_parts = []
        
        # Add user preferences if available
        user_preferences = context.get("user_preferences", {})
        if user_preferences:
            if user_preferences.get("preferred_city"):
                context_parts.append(f"Preferred city: {user_preferences['preferred_city']}")
            if user_preferences.get("property_type"):
                context_parts.append(f"Property type: {user_preferences['property_type']}")
            if user_preferences.get("min_bedrooms"):
                context_parts.append(f"Minimum bedrooms: {user_preferences['min_bedrooms']}")
            if user_preferences.get("max_price"):
                context_parts.append(f"Maximum price: ${user_preferences['max_price']:,}")
        
        # Add current location if available
        current_location = context.get("current_location")
        if current_location:
            context_parts.append(f"Current location: {current_location}")
        
        return "; ".join(context_parts) if context_parts else ""
    
    def _generate_fallback_summary(self, user_message: str) -> str:
        """Generates a simple fallback summary when OpenAI fails"""
        # Extract key words and create a basic summary
        message_lower = user_message.lower()
        
        # Look for property types
        property_types = ["house", "apartment", "condo", "townhouse", "villa", "studio", "loft"]
        found_type = next((pt for pt in property_types if pt in message_lower), "property")
        
        # Look for location indicators
        location_indicators = ["in", "near", "around", "close to", "at"]
        location_part = ""
        for indicator in location_indicators:
            if indicator in message_lower:
                # Try to extract what comes after the location indicator
                parts = message_lower.split(indicator, 1)
                if len(parts) > 1:
                    location_part = f" {indicator} {parts[1].split()[0]}" if parts[1].split() else ""
                break
        
        return f"User looking for {found_type}{location_part}"
