"""
Property-related endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import logging
from src.models.property import (
    PropertySearchRequest, PropertySearchResponse,
    PropertyDetailResponse,
    POISearchRequest, POISearchResponse,
    PropertyCompareRequest, PropertyCompareResponse
)
from src.services.weaviate import WeaviateService
from src.api.dependencies import get_weaviate_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Properties"])

@router.post("/search", response_model=PropertySearchResponse)
async def search_properties(
    request: PropertySearchRequest,
    weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    """
    POST /search
    Input: text + filters (price, beds, baths, radius, lat/lon)
    Output: list of properties + metadata
    """
    try:
        search_response = weaviate_service.search_properties(request)
        return search_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in property search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search error"
        )

@router.get("/property/{property_id}", response_model=PropertyDetailResponse)
async def get_property_detail(
    property_id: str,
    weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    """
    GET /property/{id}
    Detail + similar recommendations (vector query nearObject or more_like_this via hybrid)
    """
    try:
        if not property_id or not property_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid property ID"
            )
        
        property_detail = weaviate_service.get_property_detail(property_id.strip())
        if not property_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        return property_detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property detail {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/property/{property_id}/pois", response_model=POISearchResponse)
async def get_property_pois(
    property_id: str,
    category: Optional[str] = None,
    radius: int = 1500,
    limit: int = 10,
    weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    """
    GET /property/{id}/pois?category=school&radius=1500
    Calls Weaviate(POI). Returns top N by distance.
    """
    try:
        if not property_id or not property_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid property ID"
            )
        
        if not 1 <= radius <= 10000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Radius must be between 1 and 10000 meters"
            )
        
        if not 1 <= limit <= 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 50"
            )
        
        poi_request = POISearchRequest(
            property_id=property_id.strip(),
            category=category,
            radius=radius,
            limit=limit
        )
        
        pois_response = weaviate_service.search_pois(poi_request)
        return pois_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting POIs for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/compare", response_model=PropertyCompareResponse)
async def compare_properties(
    request: PropertyCompareRequest,
    weaviate_service: WeaviateService = Depends(get_weaviate_service)
):
    """
    POST /compare
    Input: list of IDs, returns aligned comparison (table) and generated pros/cons
    """
    try:
        comparison_response = weaviate_service.compare_properties(request)
        return comparison_response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Comparison error"
        )

