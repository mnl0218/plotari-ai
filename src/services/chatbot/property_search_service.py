"""
Service for property searches and related operations
Handles basic searches, searches near POIs, details and comparisons
"""
from typing import List, Dict, Any, Optional
from .interfaces import PropertySearchInterface
from src.services.weaviate import WeaviateService
from src.models.property import Property, PropertySearchRequest, PropertyCompareRequest
import logging

logger = logging.getLogger(__name__)


class PropertySearchService(PropertySearchInterface):
    """Service for property searches and related operations"""
    
    def __init__(self, weaviate_service: Optional[WeaviateService] = None):
        self.weaviate_service = weaviate_service
    
    def search_properties(self, search_intent: Dict[str, Any]) -> List[Property]:
        """Searches properties based on search intent"""
        try:
            if not search_intent.get("query") or not self.weaviate_service:
                return []
            
            # Special mode: search properties near POIs
            if search_intent.get("search_mode") == "near_pois":
                return self.search_properties_near_pois(search_intent)
            
            # Build search request with clean values
            filters = search_intent.get("filters", {})
            
            # Helper function to clean empty string values
            def clean_value(value):
                if isinstance(value, str) and not value.strip():
                    return None
                return value
            
            search_request = PropertySearchRequest(
                query=search_intent["query"],
                limit=10,
                city=clean_value(filters.get("city")),
                state=clean_value(filters.get("state")),
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
    
    def search_properties_near_pois(self, search_intent: Dict[str, Any]) -> List[Property]:
        """Searches properties near specific POIs"""
        try:
            filters = search_intent.get("filters", {})
            poi_category = filters.get("poi_category")
            poi_radius = filters.get("poi_radius", 2000)  # Wider default radius
            
            if not self.weaviate_service:
                return []
            
            # First search all POIs of the specified category
            pois = self.weaviate_service._get_pois_by_category(poi_category)
            
            if not pois:
                logger.info(f"No POIs found for category: {poi_category}")
                return []
            
            # Search properties near each POI
            all_properties = []
            for poi in pois:
                if hasattr(poi.geo, 'latitude') and hasattr(poi.geo, 'longitude'):
                    # Search properties within radius of POI
                    search_request = PropertySearchRequest(
                        query=search_intent["query"],
                        latitude=poi.geo.latitude,
                        longitude=poi.geo.longitude,
                        radius=poi_radius,
                        limit=5  # Maximum 5 per POI
                    )
                    
                    search_response = self.weaviate_service.search_properties(search_request)
                    all_properties.extend(search_response.properties)
            
            # Remove duplicates and limit results
            unique_properties = []
            seen_zpids = set()
            for prop in all_properties:
                if prop.zpid not in seen_zpids:
                    unique_properties.append(prop)
                    seen_zpids.add(prop.zpid)
                    if len(unique_properties) >= 10:  # Maximum 10 properties
                        break
            
            return unique_properties
            
        except Exception as e:
            logger.error(f"Error searching properties near POIs: {e}")
            return []
    
    def get_property_detail(self, search_intent: Dict[str, Any]) -> Optional[Any]:
        """Gets property detail"""
        try:
            property_id = search_intent.get("property_id")
            if not property_id or not self.weaviate_service:
                return None
            
            return self.weaviate_service.get_property_detail(property_id)
            
        except Exception as e:
            logger.error(f"Error getting property detail: {e}")
            return None
    
    def compare_properties(self, search_intent: Dict[str, Any]) -> List[Property]:
        """Compares properties based on intent"""
        try:
            property_ids = search_intent.get("property_ids", [])
            if len(property_ids) < 2 or not self.weaviate_service:
                return []
            
            compare_request = PropertyCompareRequest(property_ids=property_ids)
            compare_response = self.weaviate_service.compare_properties(compare_request)
            return compare_response.properties
            
        except Exception as e:
            logger.error(f"Error comparing properties: {e}")
            return []
