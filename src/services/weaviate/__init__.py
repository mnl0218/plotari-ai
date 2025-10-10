"""
Weaviate services module
Contains all specialized services for Weaviate operations
"""

from .weaviate_service import WeaviateService
from .interfaces import (
    WeaviateConnectionInterface,
    WeaviateSearchInterface,
    WeaviatePropertyInterface,
    WeaviatePOIInterface,
    WeaviateComparisonInterface,
    WeaviateEmbeddingInterface,
    WeaviateDataConverterInterface
)
from .connection_service import WeaviateConnectionService
from .embedding_service import WeaviateEmbeddingService
from .data_converter_service import WeaviateDataConverterService
from .search_service import WeaviateSearchService
from .property_service import WeaviatePropertyService
from .poi_service import WeaviatePOIService
from .comparison_service import WeaviateComparisonService
from .deletion_service import WeaviateDeletionService

__all__ = [
    # Main service
    'WeaviateService',
    
    # Interfaces
    'WeaviateConnectionInterface',
    'WeaviateSearchInterface',
    'WeaviatePropertyInterface',
    'WeaviatePOIInterface',
    'WeaviateComparisonInterface',
    'WeaviateEmbeddingInterface',
    'WeaviateDataConverterInterface',
    
    # Specialized services
    'WeaviateConnectionService',
    'WeaviateEmbeddingService',
    'WeaviateDataConverterService',
    'WeaviateSearchService',
    'WeaviatePropertyService',
    'WeaviatePOIService',
    'WeaviateComparisonService',
    'WeaviateDeletionService'
]
