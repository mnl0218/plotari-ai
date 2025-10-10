"""
Weaviate deletion endpoints
Handles deletion operations for Weaviate data
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from datetime import datetime
from src.services.weaviate import WeaviateDeletionService
from src.api.dependencies import get_deletion_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/delete", tags=["Deletion"])

@router.delete("/properties/all")
async def delete_all_properties(
    deletion_service: WeaviateDeletionService = Depends(get_deletion_service)
):
    """
    Delete all properties from Weaviate Property collection
    
    ⚠️ WARNING: This will DELETE ALL properties from Weaviate!
    """
    try:
        logger.info("Starting deletion of all properties from Weaviate")
        result = deletion_service.delete_all_properties()
        
        if result.get("success"):
            return {
                "success": True,
                "message": "All properties deleted successfully",
                "result": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Failed to delete properties")
            )
            
    except Exception as e:
        logger.error(f"Error deleting all properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all properties: {str(e)}"
        )

@router.delete("/properties/by-date")
async def delete_properties_by_date(
    since: str,  # ISO format datetime string
    deletion_service: WeaviateDeletionService = Depends(get_deletion_service)
):
    """
    Delete properties updated since a specific datetime
    
    Args:
        since: ISO format datetime string (e.g., "2024-01-01T00:00:00")
    """
    try:
        # Parse datetime string
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        
        logger.info(f"Starting deletion of properties updated since: {since_dt}")
        result = deletion_service.delete_properties_by_date(since_dt)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Properties deleted successfully",
                "result": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Failed to delete properties")
            )
            
    except ValueError as e:
        logger.error(f"Invalid datetime format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid datetime format. Use ISO format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error deleting properties by date: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete properties by date: {str(e)}"
        )

@router.delete("/properties/{zpid}")
async def delete_property_by_zpid(
    zpid: str,
    deletion_service: WeaviateDeletionService = Depends(get_deletion_service)
):
    """
    Delete a specific property by zpid
    
    Args:
        zpid: Property ID to delete
    """
    try:
        logger.info(f"Starting deletion of property with zpid: {zpid}")
        result = deletion_service.delete_property_by_zpid(zpid)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Property deleted successfully",
                "result": result
            }
        else:
            if "not found" in result.get("message", "").lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.get("message", "Property not found")
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("message", "Failed to delete property")
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting property by zpid {zpid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete property: {str(e)}"
        )

@router.delete("/properties/bulk")
async def delete_properties_by_zpids(
    zpids: List[str],
    deletion_service: WeaviateDeletionService = Depends(get_deletion_service)
):
    """
    Delete multiple properties by their zpids
    
    Args:
        zpids: List of property IDs to delete
    """
    try:
        if not zpids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No zpids provided"
            )
        
        logger.info(f"Starting bulk deletion of {len(zpids)} properties")
        result = deletion_service.delete_properties_by_zpids(zpids)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Bulk deletion completed",
                "result": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Failed to delete properties")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk deletion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete properties: {str(e)}"
        )

@router.get("/properties/status")
async def get_deletion_status(
    deletion_service: WeaviateDeletionService = Depends(get_deletion_service)
):
    """
    Get the current status of Weaviate Property collection
    
    Returns:
        Status information including total count
    """
    try:
        # Get Weaviate service to check status
        weaviate_service = deletion_service.weaviate_service
        weaviate_service.connection_service.ensure_connection()
        prop_col = weaviate_service.connection_service.client.collections.get("Property")
        
        # Get total count
        total_count = prop_col.aggregate.over_all(total_count=True).total_count
        
        return {
            "success": True,
            "message": "Deletion status retrieved successfully",
            "status": {
                "total_properties": total_count,
                "collection_name": "Property",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting deletion status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get deletion status: {str(e)}"
        )

@router.delete("/pois/all")
async def delete_all_pois(
    deletion_service: WeaviateDeletionService = Depends(get_deletion_service)
):
    """
    Delete all POIs from Weaviate POI collection
    """
    try:
        logger.info("Starting deletion of all POIs from Weaviate")
        result = deletion_service.delete_all_pois()
        return result
    except Exception as e:
        logger.error(f"Error deleting all POIs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all POIs: {str(e)}"
        )