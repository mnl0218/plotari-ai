"""
Interfaces/Protocols for Weaviate services
Defines clear contracts between different Weaviate services
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from src.models.property import (
    Property, PropertySearchRequest, PropertySearchResponse,
    PropertyDetailResponse, POI, POISearchRequest, POISearchResponse,
    PropertyCompareRequest, PropertyCompareResponse, Neighborhood,
    GeoCoordinate
)

class WeaviateConnectionInterface(ABC):
    """Interface for Weaviate connection management"""
    
    @abstractmethod
    def connect(self) -> None:
        """Establishes connection with Weaviate"""
        pass
    
    @abstractmethod
    def ensure_connection(self) -> None:
        """Ensures connection is active, reconnects if necessary"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Checks if connection is active"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Closes the connection"""
        pass

class WeaviateSearchInterface(ABC):
    """Interface for core search operations"""
    
    @abstractmethod
    def search_properties(self, search_request: PropertySearchRequest) -> PropertySearchResponse:
        """Searches properties using hybrid search with filters"""
        pass

class WeaviatePropertyInterface(ABC):
    """Interface for property-specific operations"""
    
    @abstractmethod
    def get_property_detail(self, property_id: str) -> Optional[PropertyDetailResponse]:
        """Gets property detail with similar recommendations"""
        pass
    
    @abstractmethod
    def find_similar_properties(self, property_obj: Property, limit: int) -> List[Property]:
        """Finds similar properties using vector search"""
        pass

class WeaviatePOIInterface(ABC):
    """Interface for POI operations"""
    
    @abstractmethod
    def search_pois(self, poi_request: POISearchRequest) -> POISearchResponse:
        """Searches POIs near a property"""
        pass
    
    @abstractmethod
    def get_pois_by_category(self, category: str) -> List[POI]:
        """Gets all POIs of a specific category"""
        pass

class WeaviateComparisonInterface(ABC):
    """Interface for property comparison operations"""
    
    @abstractmethod
    def compare_properties(self, compare_request: PropertyCompareRequest) -> PropertyCompareResponse:
        """Compares properties and generates comparison table with pros/cons"""
        pass

class WeaviateEmbeddingInterface(ABC):
    """Interface for embedding generation and AI operations"""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generates embedding for text using OpenAI"""
        pass
    
    @abstractmethod
    def generate_pros_cons_with_ai(self, property_obj: Property, all_properties: List[Property]) -> Tuple[List[str], List[str]]:
        """Generates pros and cons using AI"""
        pass

class WeaviateDataConverterInterface(ABC):
    """Interface for data conversion and transformation"""
    
    @abstractmethod
    def convert_geo_coordinate(self, geo_data: Any) -> GeoCoordinate:
        """Converts geo data to GeoCoordinate object"""
        pass
    
    @abstractmethod
    def convert_property_from_weaviate(self, obj: Any) -> Property:
        """Converts Weaviate object to Property"""
        pass
    
    @abstractmethod
    def convert_poi_from_weaviate(self, obj: Any) -> POI:
        """Converts Weaviate object to POI"""
        pass
    
    @abstractmethod
    def convert_neighborhood_from_weaviate(self, obj: Any) -> Neighborhood:
        """Converts Weaviate object to Neighborhood"""
        pass
