"""
Service for property comparison operations
Handles property comparison and AI-powered pros/cons generation
"""
from typing import List, Dict, Any, Tuple
from src.models.property import Property, PropertyCompareRequest, PropertyCompareResponse
from .interfaces import WeaviateComparisonInterface
from .connection_service import WeaviateConnectionService
from .embedding_service import WeaviateEmbeddingService
from .data_converter_service import WeaviateDataConverterService
import logging

logger = logging.getLogger(__name__)


class WeaviateComparisonService(WeaviateComparisonInterface):
    """Service for handling property comparison operations"""
    
    def __init__(self, connection_service: WeaviateConnectionService,
                 embedding_service: WeaviateEmbeddingService,
                 data_converter_service: WeaviateDataConverterService):
        self.connection_service = connection_service
        self.embedding_service = embedding_service
        self.data_converter_service = data_converter_service
    
    def compare_properties(self, compare_request: PropertyCompareRequest) -> PropertyCompareResponse:
        """Compares properties and generates comparison table with pros/cons"""
        try:
            self.connection_service.ensure_connection()
            
            # Get property collection
            prop_col = self.connection_service.client.collections.get("Property")
            
            # Get all properties
            properties = []
            for property_id in compare_request.property_ids:
                result = prop_col.query.bm25(
                    query=property_id,
                    limit=1,
                    return_properties=[
                        "zpid", "address", "city", "state", "zipcode",
                        "price", "bedrooms", "bathrooms", "living_area", 
                        "year_built", "lot_size", "description", "features",
                        "neighborhood_text", "geo", "search_corpus"
                    ]
                )
                
                if result.objects and result.objects[0].properties["zpid"] == property_id:
                    prop_data = dict(result.objects[0].properties)
                    # Convert geo coordinates if necessary
                    if prop_data.get("geo"):
                        prop_data["geo"] = self.data_converter_service.convert_geo_coordinate(prop_data["geo"])
                    properties.append(Property(**prop_data))
            
            if len(properties) != len(compare_request.property_ids):
                raise ValueError("Not all specified properties were found")
            
            # Create comparison table
            comparison_table = self._build_comparison_table(properties)
            
            # Generate pros and cons using AI
            pros_cons = {}
            try:
                for prop in properties:
                    pros, cons = self.embedding_service.generate_pros_cons_with_ai(prop, properties)
                    pros_cons[prop.zpid] = {"pros": pros, "cons": cons}
            except Exception as e:
                logger.warning(f"Error generating pros/cons: {e}")
                # Fallback: basic pros/cons
                for prop in properties:
                    pros_cons[prop.zpid] = {
                        "pros": ["Accessible location", "Competitive price"],
                        "cons": ["Limited information available"]
                    }
            
            return PropertyCompareResponse(
                properties=properties,
                comparison_table=comparison_table,
                pros_cons=pros_cons
            )
            
        except Exception as e:
            logger.error(f"Error comparing properties: {e}")
            raise
    
    def _build_comparison_table(self, properties: List[Property]) -> Dict[str, List[Any]]:
        """Builds comparison table from properties"""
        return {
            "address": [p.address for p in properties],
            "city": [p.city for p in properties],
            "price": [p.price for p in properties],
            "bedrooms": [p.bedrooms for p in properties],
            "bathrooms": [p.bathrooms for p in properties],
            "living_area": [p.living_area for p in properties],
            "year_built": [p.year_built for p in properties],
            "lot_size": [p.lot_size for p in properties],
            "neighborhood": [p.neighborhood_text for p in properties]
        }
    
    def _generate_pros_cons(self, property_obj: Property, all_properties: List[Property]) -> Tuple[List[str], List[str]]:
        """Generates pros and cons for a property using AI"""
        return self.embedding_service.generate_pros_cons_with_ai(property_obj, all_properties)
