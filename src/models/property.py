"""
Data models for real estate properties, POIs and neighborhoods
Based on the insert_test_data.py schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum
import re

class GeoCoordinate(BaseModel):
    """Geographic coordinates"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")

class Neighborhood(BaseModel):
    """Model for a neighborhood"""
    name: str = Field(..., max_length=200, description="Neighborhood name")
    city: str = Field(..., max_length=100, description="City")
    info: Optional[str] = Field(None, max_length=1000, description="Neighborhood information")
    geo_center: GeoCoordinate = Field(..., description="Geographic center of the neighborhood")
    search_corpus: Optional[str] = Field(None, max_length=2000, description="Search corpus")

class POI(BaseModel):
    """Model for a point of interest (POI)"""
    name: str = Field(..., max_length=200, description="POI name")
    category: str = Field(..., max_length=100, description="POI category")
    rating: Optional[float] = Field(None, ge=0, le=5, description="POI rating")
    source: Optional[str] = Field(None, max_length=100, description="Data source")
    geo: GeoCoordinate = Field(..., description="Geographic location")
    search_corpus: Optional[str] = Field(None, max_length=2000, description="Search corpus")

class Property(BaseModel):
    """Model for a real estate property"""
    zpid: str = Field(..., description="Unique property ID")
    address: str = Field(..., max_length=500, description="Property address")
    city: str = Field(..., max_length=100, description="City")
    state: str = Field(..., max_length=50, description="State")
    zipcode: str = Field(..., max_length=10, description="ZIP code")
    property_id: int = Field(..., description="Internal property table ID")
    price: Optional[float] = Field(None, ge=0, description="Property price")
    bedrooms: Optional[float] = Field(None, ge=0, le=20, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, ge=0, le=20, description="Number of bathrooms")
    living_area: Optional[float] = Field(None, ge=0, description="Living area in square feet")
    year_built: Optional[float] = Field(None, ge=1800, le=2030, description="Year built")
    lot_size: Optional[float] = Field(None, ge=0, description="Lot size in square feet")
    description: Optional[str] = Field(None, max_length=5000, description="Property description")
    neighborhood_text: Optional[str] = Field(None, max_length=200, description="Neighborhood")
    geo: GeoCoordinate = Field(..., description="Geographic location")
    search_corpus: Optional[str] = Field(None, max_length=2000, description="Search corpus")
    property_type: Optional[str] = Field(None, max_length=100, description="Property type")
    listing_id: Optional[int] = Field(None, description="Internal listing table ID")
    listing_type: Optional[str] = Field(None, max_length=100, description="Listing type")
    
    @validator('zpid')
    def validate_zpid(cls, v):
        """Validates the ZPID"""
        if not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('ZPID must contain only letters and numbers')
        return v
    
    @validator('zipcode')
    def validate_zipcode(cls, v):
        """Validates the ZIP code"""
        if not re.match(r'^\d{5}(-\d{4})?$', v):
            raise ValueError('Invalid ZIP code')
        return v
    
    @validator('state')
    def validate_state(cls, v):
        """Validates the state"""
        if v is not None and v.strip():
            if len(v.strip()) != 2:
                raise ValueError('State must be a 2-letter code')
            return v.strip().upper()
        return v

class PropertySearchRequest(BaseModel):
    """Model for property search requests"""
    query: Optional[str] = Field(None, min_length=1, max_length=1000, description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    
    # Filters
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price")
    min_bedrooms: Optional[int] = Field(None, ge=0, description="Minimum number of bedrooms")
    max_bedrooms: Optional[int] = Field(None, ge=0, description="Maximum number of bedrooms")
    min_bathrooms: Optional[int] = Field(None, ge=0, description="Minimum number of bathrooms")
    max_bathrooms: Optional[int] = Field(None, ge=0, description="Maximum number of bathrooms")
    
    # Geographic filters
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude for radius search")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude for radius search")
    radius: Optional[int] = Field(None, ge=1, le=50000, description="Radius in meters for geographic search")
    
    # Other filters
    city: Optional[str] = Field(None, max_length=100, description="Filter by city")
    state: Optional[str] = Field(None, max_length=2, description="Filter by state")
    neighborhood: Optional[str] = Field(None, max_length=200, description="Filter by neighborhood")
    property_type: Optional[str] = Field(None, max_length=100, description="Property type")
    
    @validator('query')
    def validate_query(cls, v):
        """Validates the search query"""
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None
    
    @validator('state')
    def validate_state(cls, v):
        """Validates the state"""
        if v is not None and v.strip():  # Only validate if not None and not empty
            if len(v.strip()) != 2:
                raise ValueError('State must be a 2-letter code')
            return v.strip().upper()
        return None  # Return None for empty strings or None

class PropertySearchResponse(BaseModel):
    """Model for property search responses"""
    properties: List[Property] = Field(..., description="List of properties found")
    total_count: int = Field(..., ge=0, description="Total number of properties found")
    query: Optional[str] = Field(None, description="Original query")
    search_type: str = Field(..., description="Type of search performed")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters applied")

class PropertyDetailResponse(BaseModel):
    """Model for property detail response with recommendations"""
    property: Property = Field(..., description="Main property")
    similar_properties: List[Property] = Field(default=[], description="Similar properties")
    neighborhood: Optional[Neighborhood] = Field(None, description="Neighborhood information")

class POISearchRequest(BaseModel):
    """Model for POI search requests"""
    property_id: str = Field(..., description="Reference property ID")
    category: Optional[str] = Field(None, max_length=100, description="POI category (e.g.: school, restaurant)")
    radius: int = Field(default=1500, ge=1, le=10000, description="Radius in meters")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")

class POISearchResponse(BaseModel):
    """Model for POI search responses"""
    pois: List[POI] = Field(..., description="List of POIs found")
    property_id: str = Field(..., description="Reference property ID")
    category: Optional[str] = Field(None, description="Filtered category")
    radius: int = Field(..., description="Radius used in meters")

class PropertyCompareRequest(BaseModel):
    """Model for property comparison requests"""
    property_ids: List[str] = Field(..., min_items=2, max_items=5, description="List of property IDs to compare")
    
    @validator('property_ids')
    def validate_property_ids(cls, v):
        """Validates that there are no duplicate IDs"""
        if len(v) != len(set(v)):
            raise ValueError('Duplicate IDs are not allowed')
        return v

class PropertyCompareResponse(BaseModel):
    """Model for property comparison responses"""
    properties: List[Property] = Field(..., description="Properties compared")
    comparison_table: Dict[str, List[Any]] = Field(..., description="Comparison table")
    pros_cons: Dict[str, Dict[str, List[str]]] = Field(..., description="Pros and cons of each property")

class ChatRequest(BaseModel):
    """Model for chat requests"""
    model_config = ConfigDict(populate_by_name=True)
    
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    user_id: str = Field(..., min_length=1, max_length=100, description="User ID for conversation persistence")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context (propertyId, city, etc.)")
    session_id: Optional[str] = Field(default=None, alias="sessionId", description="Session ID for conversation persistence")
    
    @validator('message')
    def validate_message(cls, v):
        """Validates the user message"""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """Validates the user ID"""
        if not v or not v.strip():
            raise ValueError('User ID cannot be empty')
        return v.strip()

class ChatResponse(BaseModel):
    """Model for chat responses"""
    message: str = Field(..., min_length=1, max_length=10000, description="Assistant response")
    properties_found: Optional[List[Property]] = Field(default=None, description="Related properties found")
    pois_found: Optional[List[POI]] = Field(default=None, description="Related POIs found")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class POIEnrichmentRequest(BaseModel):
    """Model for POI enrichment requests"""
    since_date: str = Field(..., description="ISO 8601 date to filter properties (YYYY-MM-DD or datetime)")
    radius: int = Field(default=1000, ge=100, le=5000, description="Search radius in meters for each property")
    amenities: List[str] = Field(..., min_items=1, max_items=10, description="List of amenity types to search (restaurant, school, etc.)")
    limit_per_property: int = Field(default=20, ge=1, le=50, description="Maximum POIs per property")
    
    @validator('amenities')
    def validate_amenities(cls, v):
        """Validates amenity types"""
        if not v:
            raise ValueError('At least one amenity type is required')
        # Remove duplicates and empty strings
        return list(set(filter(None, [a.strip().lower() for a in v])))

class POIEnrichmentResponse(BaseModel):
    """Model for POI enrichment responses"""
    status: str = Field(..., description="Status of the enrichment process")
    properties_processed: int = Field(..., ge=0, description="Number of properties processed")
    total_pois_found: int = Field(..., ge=0, description="Total POIs found from OSM")
    total_pois_saved: int = Field(..., ge=0, description="Total POIs saved to Weaviate")
    amenities_searched: List[str] = Field(..., description="Amenity types searched")
    errors: Optional[List[str]] = Field(default=None, description="List of errors encountered")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")