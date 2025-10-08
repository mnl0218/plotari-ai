"""
Service for POI operations
Handles POI searches and category-based queries
"""
from typing import List
from weaviate.classes.query import Filter, GeoCoordinate as QueryGeo
from src.models.property import POI, POISearchRequest, POISearchResponse
from .interfaces import WeaviatePOIInterface
from .connection_service import WeaviateConnectionService
from .data_converter_service import WeaviateDataConverterService
import logging

logger = logging.getLogger(__name__)


class WeaviatePOIService(WeaviatePOIInterface):
    """Service for handling POI operations"""
    
    def __init__(self, connection_service: WeaviateConnectionService,
                 data_converter_service: WeaviateDataConverterService):
        self.connection_service = connection_service
        self.data_converter_service = data_converter_service
    
    def search_pois(self, poi_request: POISearchRequest) -> POISearchResponse:
        """Searches POIs near a property"""
        try:
            self.connection_service.ensure_connection()
            
            # Get collections
            prop_col = self.connection_service.client.collections.get("Property")
            poi_col = self.connection_service.client.collections.get("POI")
            
            # Get property location
            prop_result = prop_col.query.bm25(
                query=poi_request.property_id,
                limit=1,
                return_properties=["geo"]
            )
            
            if not prop_result.objects:
                raise ValueError(f"Property {poi_request.property_id} not found")
            
            prop_geo = prop_result.objects[0].properties["geo"]
            
            # Extract coordinates from GeoCoordinate
            lat, lon = self.data_converter_service._extract_geo_coordinates(prop_geo)
            
            # Build filters for POIs
            filters = Filter.by_property("geo").within_geo_range(
                coordinate=QueryGeo(latitude=lat, longitude=lon),
                distance=poi_request.radius
            )
            
            # Add category filter if specified
            if poi_request.category:
                filters = filters & Filter.by_property("category").equal(poi_request.category)
            
            # Search POIs using fetch_objects with filters
            poi_result = poi_col.query.fetch_objects(
                limit=poi_request.limit,
                filters=filters,
                return_properties=["name", "category", "rating", "source", "geo", "search_corpus"]
            )
            
            # Convert results to POI objects
            pois = self.data_converter_service.convert_pois_list(poi_result.objects)
            
            return POISearchResponse(
                pois=pois,
                property_id=poi_request.property_id,
                category=poi_request.category,
                radius=poi_request.radius
            )
            
        except Exception as e:
            logger.error(f"Error searching POIs: {e}")
            raise
    
    def get_pois_by_category(self, category: str) -> List[POI]:
        """Gets all POIs of a specific category"""
        try:
            if not category:
                return []
                
            self.connection_service.ensure_connection()
            poi_col = self.connection_service.client.collections.get("POI")
            
            # Search POIs by category
            category_filter = Filter.by_property("category").equal(category)
            result = poi_col.query.fetch_objects(
                limit=50,  # Maximum 50 POIs
                filters=category_filter,
                return_properties=["name", "category", "rating", "source", "geo", "search_corpus"]
            )
            
            # Convert results to POI objects
            return self.data_converter_service.convert_pois_list(result.objects)
            
        except Exception as e:
            logger.error(f"Error getting POIs by category {category}: {e}")
            return []
    
    def _convert_poi_data(self, poi_data: dict) -> POI:
        """Converts POI data to POI object"""
        try:
            # Convert geo coordinates if necessary
            if poi_data.get("geo"):
                poi_data["geo"] = self.data_converter_service.convert_geo_coordinate(poi_data["geo"])
            
            return POI(**poi_data)
        except Exception as e:
            logger.error(f"Error converting POI data: {e}")
            raise
