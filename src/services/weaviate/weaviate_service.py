"""
Main Weaviate service - Refactored
Orchestrates all specialized Weaviate services
"""
from typing import List, Optional
from src.models.property import (
    Property, PropertySearchRequest, PropertySearchResponse,
    PropertyDetailResponse, POI, POISearchRequest, POISearchResponse,
    PropertyCompareRequest, PropertyCompareResponse
)
from .connection_service import WeaviateConnectionService
from .embedding_service import WeaviateEmbeddingService
from .data_converter_service import WeaviateDataConverterService
from .search_service import WeaviateSearchService
from .property_service import WeaviatePropertyService
from .poi_service import WeaviatePOIService
from .comparison_service import WeaviateComparisonService
import logging

logger = logging.getLogger(__name__)


class WeaviateService:
    """Main Weaviate service - Refactored"""
    
    def __init__(self):
        # Initialize specialized services
        self.connection_service = WeaviateConnectionService()
        self.embedding_service = WeaviateEmbeddingService()
        self.data_converter_service = WeaviateDataConverterService()
        
        # Initialize services that depend on the above
        self.search_service = WeaviateSearchService(
            self.connection_service, 
            self.embedding_service, 
            self.data_converter_service
        )
        self.property_service = WeaviatePropertyService(
            self.connection_service, 
            self.embedding_service, 
            self.data_converter_service
        )
        self.poi_service = WeaviatePOIService(
            self.connection_service, 
            self.data_converter_service
        )
        self.comparison_service = WeaviateComparisonService(
            self.connection_service, 
            self.embedding_service, 
            self.data_converter_service
        )
        
        logger.info("WeaviateService refactored initialized successfully")
    
    def search_properties(self, search_request: PropertySearchRequest) -> PropertySearchResponse:
        """Searches properties using hybrid search with filters"""
        return self.search_service.search_properties(search_request)
    
    def get_property_detail(self, property_id: str) -> Optional[PropertyDetailResponse]:
        """Gets property detail with similar recommendations"""
        return self.property_service.get_property_detail(property_id)
    
    def search_pois(self, poi_request: POISearchRequest) -> POISearchResponse:
        """Searches POIs near a property"""
        return self.poi_service.search_pois(poi_request)
    
    def compare_properties(self, compare_request: PropertyCompareRequest) -> PropertyCompareResponse:
        """Compares properties and generates comparison table with pros/cons"""
        return self.comparison_service.compare_properties(compare_request)
    
    def _get_pois_by_category(self, category: str) -> List[POI]:
        """Gets all POIs of a specific category (for internal use)"""
        return self.poi_service.get_pois_by_category(category)
    
    def close(self) -> None:
        """Closes the connection with Weaviate"""
        self.connection_service.close()
    
    def is_connected(self) -> bool:
        """Checks if connection is active"""
        return self.connection_service.is_connected()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
