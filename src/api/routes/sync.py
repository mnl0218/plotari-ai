"""
Property synchronization endpoints
"""
from fastapi import APIRouter, Depends
import logging
from datetime import datetime
from src.services.sync import PropertySyncService
from src.api.dependencies import get_sync_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["Synchronization"])

@router.post("/properties/full")
async def sync_all_properties(
    batch_size: int = 100,
    sync_service: PropertySyncService = Depends(get_sync_service)
):
    """
    Synchronize all properties from Supabase to Weaviate
    
    Args:
        batch_size: Number of properties to process in each batch (default: 100)
    """
    try:
        logger.info(f"Starting full property synchronization with batch size: {batch_size}")
        result = sync_service.sync_all_properties(batch_size=batch_size)
        
        return {
            "success": True,
            "message": "Full property synchronization completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in full property synchronization: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to synchronize properties"
        }

@router.post("/properties/incremental")
async def sync_properties_incremental(
    since: str,  # ISO format datetime string
    batch_size: int = 100,
    sync_service: PropertySyncService = Depends(get_sync_service)
):
    """
    Synchronize properties updated since a specific datetime
    
    Args:
        since: ISO format datetime string (e.g., "2024-01-01T00:00:00")
        batch_size: Number of properties to process in each batch (default: 100)
    """
    try:
        # Parse datetime string
        since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        
        logger.info(f"Starting incremental property synchronization since: {since_dt}")
        result = sync_service.sync_properties_updated_since(since_dt, batch_size=batch_size)
        
        return {
            "success": True,
            "message": "Incremental property synchronization completed",
            "result": result
        }
    except ValueError as e:
        logger.error(f"Invalid datetime format: {e}")
        return {
            "success": False,
            "error": f"Invalid datetime format. Use ISO format: {str(e)}",
            "message": "Failed to parse datetime"
        }
    except Exception as e:
        logger.error(f"Error in incremental property synchronization: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to synchronize properties"
        }

@router.post("/properties/{property_id}")
async def sync_single_property(
    property_id: str,
    sync_service: PropertySyncService = Depends(get_sync_service)
):
    """
    Synchronize a single property by ID from Supabase to Weaviate
    
    Args:
        property_id: Property ID to synchronize
    """
    try:
        logger.info(f"Starting single property synchronization: {property_id}")
        result = sync_service.sync_single_property(property_id)
        
        return {
            "success": result.get("success", False),
            "message": "Single property synchronization completed" if result.get("success") else "Failed to synchronize property",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in single property synchronization: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to synchronize property"
        }

@router.get("/properties/status")
async def get_sync_status(
    sync_service: PropertySyncService = Depends(get_sync_service)
):
    """
    Get the current synchronization status between Supabase and Weaviate
    
    Returns:
        Status information including counts from both systems
    """
    try:
        status = sync_service.get_sync_status()
        
        return {
            "success": True,
            "message": "Sync status retrieved successfully",
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get sync status"
        }

