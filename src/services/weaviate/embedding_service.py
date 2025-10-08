"""
Service for embedding generation and AI operations
Handles OpenAI embeddings and AI-powered content generation
"""
from typing import List, Tuple
from openai import OpenAI
from src.config.settings import settings
from src.models.property import Property
from .interfaces import WeaviateEmbeddingInterface
import logging
import json

logger = logging.getLogger(__name__)


class WeaviateEmbeddingService(WeaviateEmbeddingInterface):
    """Service for handling embedding generation and AI operations"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generates embedding for text using OpenAI"""
        try:
            if not text:
                return []
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def generate_pros_cons_with_ai(self, property_obj: Property, all_properties: List[Property]) -> Tuple[List[str], List[str]]:
        """Generates pros and cons using AI"""
        try:
            # Create comparison context
            context = f"Property: {property_obj.address}, {property_obj.city}\n"
            context += f"Price: ${property_obj.price:,}\n"
            context += f"Bedrooms: {property_obj.bedrooms}, Bathrooms: {property_obj.bathrooms}\n"
            context += f"Area: {property_obj.living_area} sqft\n"
            context += f"Year: {property_obj.year_built}\n"
            
            # Add context of other properties for comparison
            other_props = [p for p in all_properties if p.zpid != property_obj.zpid]
            if other_props:
                context += "\nOther properties in comparison:\n"
                for prop in other_props:
                    context += f"- {prop.address}: ${prop.price:,}, {prop.bedrooms}br/{prop.bathrooms}ba, {prop.living_area}sqft\n"
            
            prompt = f"""
            Analyze the following Plotari property and generate 3 pros and 3 cons based on its characteristics and comparison with other similar properties.
            
            {context}
            
            Respond in JSON format:
            {{
                "pros": ["pro1", "pro2", "pro3"],
                "cons": ["con1", "con2", "con3"]
            }}
            
            The pros and cons should be specific, objective, and useful for a potential buyer.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            return result["pros"], result["cons"]
            
        except Exception as e:
            logger.warning(f"Error generating pros/cons with OpenAI: {e}")
            # Fallback basic pros/cons
            pros = ["Accessible location", "Competitive price", "Basic features"]
            cons = ["Limited information", "Requires more research", "Comparison needed"]
            return pros, cons
    
    def _call_openai_embedding(self, text: str) -> List[float]:
        """Internal method to call OpenAI embedding API"""
        return self.generate_embedding(text)
    
    def _call_openai_completion(self, prompt: str) -> str:
        """Internal method to call OpenAI completion API"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI completion: {e}")
            return ""
