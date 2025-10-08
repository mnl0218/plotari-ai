"""
Service for POI searches and related operations (Points of Interest)
Handles searches for points of interest near properties
"""
from typing import List, Dict, Any, Optional
from .interfaces import POISearchInterface
from src.services.weaviate import WeaviateService
from src.models.property import POI, POISearchRequest
import logging

logger = logging.getLogger(__name__)


class POISearchService(POISearchInterface):
    """Service for POI searches and related operations"""
    
    def __init__(self, weaviate_service: Optional[WeaviateService] = None):
        self.weaviate_service = weaviate_service
    
    def search_pois(self, search_intent: Dict[str, Any]) -> List[POI]:
        """Searches POIs based on intent"""
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
