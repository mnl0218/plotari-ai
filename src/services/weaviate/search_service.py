"""
Service for core search operations and query building
Handles property search with filters and different search types
"""
from typing import List, Optional, Dict, Any
from weaviate.classes.query import Filter, GeoCoordinate as QueryGeo
from src.models.property import PropertySearchRequest, PropertySearchResponse
from .interfaces import WeaviateSearchInterface
from .connection_service import WeaviateConnectionService
from .embedding_service import WeaviateEmbeddingService
from .data_converter_service import WeaviateDataConverterService
import logging

logger = logging.getLogger(__name__)


class WeaviateSearchService(WeaviateSearchInterface):
    """Service for handling core search operations"""
    
    def __init__(self, connection_service: WeaviateConnectionService, 
                 embedding_service: WeaviateEmbeddingService,
                 data_converter_service: WeaviateDataConverterService):
        self.connection_service = connection_service
        self.embedding_service = embedding_service
        self.data_converter_service = data_converter_service
    
    def search_properties(self, search_request: PropertySearchRequest) -> PropertySearchResponse:
        """Searches properties using hybrid search with filters"""
        try:
            self.connection_service.ensure_connection()
            
            # Get property collection
            prop_col = self.connection_service.client.collections.get("Property")
            
            # Build filters
            filters = self._build_filters(search_request)
            
            # Generate embedding if there's a query
            query_vector = None
            if search_request.query:
                query_vector = self.embedding_service.generate_embedding(search_request.query)
            
            # Execute search based on query and vector availability
            if search_request.query and query_vector:
                result = self._execute_hybrid_search(prop_col, search_request, query_vector, filters)
                search_type = "hybrid"
                
                # Fallback: if hybrid search with filters returns 0 results, try filter-only
                if len(result.objects) == 0 and filters:
                    logger.info(f"Hybrid search returned 0 results with filters, falling back to filter-only search")
                    result = self._execute_filter_only_search(prop_col, search_request, filters)
                    search_type = "hybrid_fallback_filter"
                    
            elif search_request.query:
                result = self._execute_bm25_search(prop_col, search_request, filters)
                search_type = "bm25"
            else:
                # When there's no query, use fetch_objects with filters
                result = self._execute_filter_only_search(prop_col, search_request, filters)
                search_type = "filter"
            
            # Convert results to Property objects
            properties = self.data_converter_service.convert_properties_list(result.objects)
            
            # Build applied filters for metadata
            filters_applied = self._build_filters_metadata(search_request)
            
            return PropertySearchResponse(
                properties=properties,
                total_count=len(properties),
                query=search_request.query,
                search_type=search_type,
                filters_applied=filters_applied
            )
            
        except Exception as e:
            logger.error(f"Error in property search: {e}")
            raise
    
    def _build_filters(self, search_request: PropertySearchRequest) -> Optional[Filter]:
        """Builds filters for the search"""
        filters = []
        
        # Price filters - create separate filters for min and max
        if search_request.min_price is not None:
            filters.append(Filter.by_property("price").greater_or_equal(search_request.min_price))
        if search_request.max_price is not None:
            filters.append(Filter.by_property("price").less_or_equal(search_request.max_price))
        
        # Bedroom filters - create separate filters for min and max
        if search_request.min_bedrooms is not None:
            filters.append(Filter.by_property("bedrooms").greater_or_equal(search_request.min_bedrooms))
        if search_request.max_bedrooms is not None:
            filters.append(Filter.by_property("bedrooms").less_or_equal(search_request.max_bedrooms))
        
        # Bathroom filters - create separate filters for min and max
        if search_request.min_bathrooms is not None:
            filters.append(Filter.by_property("bathrooms").greater_or_equal(search_request.min_bathrooms))
        if search_request.max_bathrooms is not None:
            filters.append(Filter.by_property("bathrooms").less_or_equal(search_request.max_bathrooms))
        
        # City and state filters
        if search_request.city:
            filters.append(Filter.by_property("city").equal(search_request.city))
        if search_request.state:
            filters.append(Filter.by_property("state").equal(search_request.state))
        
        # Property type filter
        if search_request.property_type:
            filters.append(Filter.by_property("property_type").equal(search_request.property_type))
        
        # Geographic filter
        if (search_request.latitude is not None and 
            search_request.longitude is not None and 
            search_request.radius is not None):
            geo_filter = Filter.by_property("geo").within_geo_range(
                coordinate=QueryGeo(
                    latitude=search_request.latitude,
                    longitude=search_request.longitude
                ),
                distance=search_request.radius
            )
            filters.append(geo_filter)
        
        # Combine all filters
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
            return combined_filter
        
        return None
    
    def _execute_hybrid_search(self, collection, search_request: PropertySearchRequest, 
                              query_vector: List[float], filters: Optional[Filter]):
        """Executes hybrid search with vector and BM25
        
        Alpha=0.75 gives more weight to BM25 (keyword search) over vector search,
        which helps when filtering is involved and ensures better results when
        the query includes specific criteria like price ranges.
        """
        return collection.query.hybrid(
            query=search_request.query,
            vector=query_vector,
            alpha=0.75,  # Higher alpha = more weight to BM25 vs vector search
            limit=search_request.limit,
            filters=filters,
            return_properties=[
                "zpid", "address", "city", "state", "zipcode",
                "price", "bedrooms", "bathrooms", "living_area", 
                "year_built", "lot_size", "description", "features",
                "neighborhood_text", "property_type", "geo", "search_corpus"
            ]
        )
    
    def _execute_bm25_search(self, collection, search_request: PropertySearchRequest, 
                            filters: Optional[Filter]):
        """Executes BM25 search"""
        return collection.query.bm25(
            query=search_request.query or "*",
            limit=search_request.limit,
            filters=filters,
            return_properties=[
                "zpid", "address", "city", "state", "zipcode",
                "price", "bedrooms", "bathrooms", "living_area", 
                "year_built", "lot_size", "description", "features",
                "neighborhood_text", "property_type", "geo", "search_corpus"
            ]
        )
    
    def _execute_filter_only_search(self, collection, search_request: PropertySearchRequest, 
                                    filters: Optional[Filter]):
        """Executes filter-only search using fetch_objects"""
        return collection.query.fetch_objects(
            limit=search_request.limit,
            filters=filters,
            return_properties=[
                "zpid", "address", "city", "state", "zipcode",
                "price", "bedrooms", "bathrooms", "living_area", 
                "year_built", "lot_size", "description", "features",
                "neighborhood_text", "property_type", "geo", "search_corpus"
            ]
        )
    
    def _build_filters_metadata(self, search_request: PropertySearchRequest) -> Dict[str, Any]:
        """Builds metadata about applied filters"""
        filters_applied = {}
        
        if search_request.min_price is not None:
            filters_applied["min_price"] = search_request.min_price
        if search_request.max_price is not None:
            filters_applied["max_price"] = search_request.max_price
        if search_request.min_bedrooms is not None:
            filters_applied["min_bedrooms"] = search_request.min_bedrooms
        if search_request.max_bedrooms is not None:
            filters_applied["max_bedrooms"] = search_request.max_bedrooms
        if search_request.city:
            filters_applied["city"] = search_request.city
        if search_request.state:
            filters_applied["state"] = search_request.state
        if search_request.property_type:
            filters_applied["property_type"] = search_request.property_type
        if search_request.latitude and search_request.longitude and search_request.radius:
            filters_applied["geo_search"] = {
                "latitude": search_request.latitude,
                "longitude": search_request.longitude,
                "radius": search_request.radius
            }
        
        return filters_applied
