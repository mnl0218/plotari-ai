"""
Service for property-specific operations
Handles property detail retrieval, similar properties, and neighborhood info
"""
from typing import List, Optional
from weaviate.classes.query import Filter
from src.models.property import Property, PropertyDetailResponse, Neighborhood
from .interfaces import WeaviatePropertyInterface
from .connection_service import WeaviateConnectionService
from .embedding_service import WeaviateEmbeddingService
from .data_converter_service import WeaviateDataConverterService
import logging

logger = logging.getLogger(__name__)


class WeaviatePropertyService(WeaviatePropertyInterface):
    """Service for handling property-specific operations"""
    
    def __init__(self, connection_service: WeaviateConnectionService,
                 embedding_service: WeaviateEmbeddingService,
                 data_converter_service: WeaviateDataConverterService):
        self.connection_service = connection_service
        self.embedding_service = embedding_service
        self.data_converter_service = data_converter_service
    
    def get_property_detail(self, property_id: str) -> Optional[PropertyDetailResponse]:
        """Gets property detail with similar recommendations"""
        try:
            self.connection_service.ensure_connection()
            
            # Get collections
            prop_col = self.connection_service.client.collections.get("Property")
            neigh_col = self.connection_service.client.collections.get("Neighborhood")
            
            # Search for the property by zpid
            result = prop_col.query.bm25(
                query=property_id,
                limit=1,
                return_properties=[
                    "zpid", "address", "city", "state", "zipcode",
                    "price", "bedrooms", "bathrooms", "living_area", 
                    "year_built", "lot_size", "description", "features",
                    "neighborhood_text", "property_type", "geo", "search_corpus"
                ]
            )
            
            if not result.objects:
                return None
            
            # Get the main property
            main_prop_data = dict(result.objects[0].properties)
            if main_prop_data["zpid"] != property_id:
                return None
            
            # Convert geo coordinates if necessary
            if main_prop_data.get("geo"):
                main_prop_data["geo"] = self.data_converter_service.convert_geo_coordinate(main_prop_data["geo"])
            
            main_property = Property(**main_prop_data)
            
            # Find similar properties using vector search
            similar_properties = self.find_similar_properties(main_property, 4)
            
            # Get neighborhood information if available
            neighborhood = self.get_neighborhood_info(main_property.neighborhood_text)
            
            return PropertyDetailResponse(
                property=main_property,
                similar_properties=similar_properties,
                neighborhood=neighborhood
            )
            
        except Exception as e:
            logger.error(f"Error getting property detail {property_id}: {e}")
            raise
    
    def find_similar_properties(self, property_obj: Property, limit: int) -> List[Property]:
        """Finds similar properties using vector search"""
        try:
            if not property_obj.search_corpus:
                return []
            
            self.connection_service.ensure_connection()
            prop_col = self.connection_service.client.collections.get("Property")
            
            query_vector = self.embedding_service.generate_embedding(property_obj.search_corpus)
            if not query_vector:
                return []
            
            similar_result = prop_col.query.near_vector(
                near_vector=query_vector,
                limit=limit,
                filters=Filter.by_property("zpid").not_equal(property_obj.zpid),
                return_properties=[
                    "zpid", "address", "city", "state", "zipcode",
                    "price", "bedrooms", "bathrooms", "living_area", 
                    "year_built", "lot_size", "description", "features",
                    "neighborhood_text", "property_type", "geo", "search_corpus"
                ]
            )
            
            return self.data_converter_service.convert_properties_list(similar_result.objects)
            
        except Exception as e:
            logger.error(f"Error finding similar properties: {e}")
            return []
    
    def get_neighborhood_info(self, neighborhood_text: str) -> Optional[Neighborhood]:
        """Gets neighborhood information if available"""
        try:
            if not neighborhood_text:
                return None
            
            self.connection_service.ensure_connection()
            neigh_col = self.connection_service.client.collections.get("Neighborhood")
            
            neigh_result = neigh_col.query.bm25(
                query=neighborhood_text,
                limit=1,
                return_properties=["name", "city", "info", "geo_center", "search_corpus"]
            )
            
            if not neigh_result.objects:
                return None
            
            return self.data_converter_service.convert_neighborhood_from_weaviate(neigh_result.objects[0])
            
        except Exception as e:
            logger.warning(f"Error getting neighborhood info: {e}")
            return None
    
    def _convert_property_data(self, prop_data: dict) -> Property:
        """Converts property data to Property object"""
        try:
            # Convert geo coordinates if necessary
            if prop_data.get("geo"):
                prop_data["geo"] = self.data_converter_service.convert_geo_coordinate(prop_data["geo"])
            
            return Property(**prop_data)
        except Exception as e:
            logger.error(f"Error converting property data: {e}")
            raise
