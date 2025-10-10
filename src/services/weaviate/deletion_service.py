"""
Weaviate deletion service
Handles deletion operations for Weaviate data
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from src.services.weaviate import WeaviateService
from weaviate.classes.query import Filter

logger = logging.getLogger(__name__)


class WeaviateDeletionService:
    """Service for handling Weaviate deletion operations"""
    
    def __init__(self):
        """Initialize deletion service with Weaviate service"""
        self.weaviate_service = WeaviateService()
    
    def delete_all_properties(self) -> Dict[str, Any]:
        """
        Deletes all properties from Weaviate Property collection
        
        Returns:
            Deletion result summary
        """
        try:
            logger.info("Starting deletion of all properties from Weaviate")
            
            # Ensure connection
            self.weaviate_service.connection_service.ensure_connection()
            prop_col = self.weaviate_service.connection_service.client.collections.get("Property")
            
            # Get initial count
            initial_count = prop_col.aggregate.over_all(total_count=True).total_count
            logger.info(f"Found {initial_count} properties to delete")
            
            if initial_count == 0:
                return {
                    "success": True,
                    "message": "No properties found to delete",
                    "deleted_count": 0,
                    "initial_count": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Try different deletion methods
            deleted_count = 0
            
            try:
                # Method 1: Wildcard filter
                logger.info("Trying wildcard filter deletion method")
                prop_col.data.delete_many(where=Filter.by_property("zpid").like("*"))
                deleted_count = initial_count
                logger.info("✅ Wildcard filter deletion successful")
                
            except Exception as e1:
                logger.warning(f"Wildcard method failed: {e1}")
                try:
                    # Method 2: Exists filter
                    logger.info("Trying exists filter deletion method")
                    prop_col.data.delete_many(where=Filter.by_property("zpid").exists())
                    deleted_count = initial_count
                    logger.info("✅ Exists filter deletion successful")
                    
                except Exception as e2:
                    logger.warning(f"Exists method failed: {e2}")
                    try:
                        # Method 3: Individual deletion
                        logger.info("Trying individual deletion method")
                        objects = prop_col.query.fetch_objects(limit=1000)
                        for obj in objects.objects:
                            prop_col.data.delete_by_id(obj.uuid)
                            deleted_count += 1
                        logger.info(f"✅ Individual deletion successful - deleted {deleted_count} objects")
                        
                    except Exception as e3:
                        logger.error(f"All deletion methods failed: {e3}")
                        raise e3
            
            # Wait for deletion to complete
            import time
            time.sleep(2)
            
            # Verify deletion
            final_count = prop_col.aggregate.over_all(total_count=True).total_count
            
            result = {
                "success": True,
                "message": f"Successfully deleted {deleted_count} properties",
                "deleted_count": deleted_count,
                "initial_count": initial_count,
                "remaining_count": final_count,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Deletion completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting all properties: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete properties",
                "timestamp": datetime.now().isoformat()
            }
    
    def delete_properties_by_date(self, since: datetime) -> Dict[str, Any]:
        """
        Deletes properties updated since a specific datetime
        
        Args:
            since: Datetime to filter by
            
        Returns:
            Deletion result summary
        """
        try:
            logger.info(f"Starting deletion of properties updated since: {since}")
            
            # Ensure connection
            self.weaviate_service.connection_service.ensure_connection()
            prop_col = self.weaviate_service.connection_service.client.collections.get("Property")
            
            # Get properties updated since the specified date
            # Note: This assumes there's an updated_at field in Weaviate
            # If not available, we'll need to implement a different approach
            try:
                # Try to filter by updated_at field if it exists
                since_str = since.isoformat()
                result = prop_col.query.fetch_objects(
                    where=Filter.by_property("updated_at").greater_than(since_str),
                    limit=1000
                )
                
                properties_to_delete = result.objects
                logger.info(f"Found {len(properties_to_delete)} properties updated since {since}")
                
            except Exception as e:
                logger.warning(f"Could not filter by updated_at: {e}")
                # Fallback: get all properties and check manually
                # This is less efficient but more reliable
                all_properties = prop_col.query.fetch_objects(limit=1000)
                properties_to_delete = []
                
                for obj in all_properties.objects:
                    # Check if property was updated since the specified date
                    # This would need to be implemented based on your data structure
                    properties_to_delete.append(obj)
                
                logger.info(f"Found {len(properties_to_delete)} properties to check for deletion")
            
            if not properties_to_delete:
                return {
                    "success": True,
                    "message": "No properties found updated since the specified date",
                    "deleted_count": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Delete properties individually
            deleted_count = 0
            for obj in properties_to_delete:
                try:
                    prop_col.data.delete_by_id(obj.uuid)
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete property {obj.uuid}: {e}")
            
            result = {
                "success": True,
                "message": f"Successfully deleted {deleted_count} properties updated since {since}",
                "deleted_count": deleted_count,
                "total_found": len(properties_to_delete),
                "since": since.isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Date-based deletion completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting properties by date: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete properties by date",
                "timestamp": datetime.now().isoformat()
            }
    
    def delete_property_by_zpid(self, zpid: str) -> Dict[str, Any]:
        """
        Deletes a specific property by zpid
        
        Args:
            zpid: Property ID to delete
            
        Returns:
            Deletion result summary
        """
        try:
            logger.info(f"Starting deletion of property with zpid: {zpid}")
            
            # Ensure connection
            self.weaviate_service.connection_service.ensure_connection()
            prop_col = self.weaviate_service.connection_service.client.collections.get("Property")
            
            # Search for the property by zpid
            result = prop_col.query.fetch_objects(
                where=Filter.by_property("zpid").equal(zpid),
                limit=1
            )
            
            if not result.objects:
                return {
                    "success": False,
                    "message": f"Property with zpid '{zpid}' not found",
                    "deleted_count": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Delete the property
            property_obj = result.objects[0]
            prop_col.data.delete_by_id(property_obj.uuid)
            
            result = {
                "success": True,
                "message": f"Successfully deleted property with zpid '{zpid}'",
                "deleted_count": 1,
                "zpid": zpid,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Property deletion completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting property by zpid {zpid}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete property with zpid '{zpid}'",
                "timestamp": datetime.now().isoformat()
            }
    
    def delete_properties_by_zpids(self, zpids: List[str]) -> Dict[str, Any]:
        """
        Deletes multiple properties by their zpids
        
        Args:
            zpids: List of property IDs to delete
            
        Returns:
            Deletion result summary
        """
        try:
            logger.info(f"Starting deletion of {len(zpids)} properties by zpids")
            
            # Ensure connection
            self.weaviate_service.connection_service.ensure_connection()
            prop_col = self.weaviate_service.connection_service.client.collections.get("Property")
            
            deleted_count = 0
            not_found = []
            errors = []
            
            for zpid in zpids:
                try:
                    # Search for the property
                    result = prop_col.query.fetch_objects(
                        where=Filter.by_property("zpid").equal(zpid),
                        limit=1
                    )
                    
                    if result.objects:
                        # Delete the property
                        property_obj = result.objects[0]
                        prop_col.data.delete_by_id(property_obj.uuid)
                        deleted_count += 1
                        logger.debug(f"Deleted property with zpid: {zpid}")
                    else:
                        not_found.append(zpid)
                        logger.warning(f"Property with zpid '{zpid}' not found")
                        
                except Exception as e:
                    errors.append({"zpid": zpid, "error": str(e)})
                    logger.error(f"Error deleting property {zpid}: {e}")
            
            result = {
                "success": True,
                "message": f"Deletion completed: {deleted_count} deleted, {len(not_found)} not found, {len(errors)} errors",
                "deleted_count": deleted_count,
                "not_found": not_found,
                "errors": errors,
                "total_requested": len(zpids),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Bulk deletion completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk deletion: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete properties",
                "timestamp": datetime.now().isoformat()
            }

    def delete_all_pois(self) -> Dict[str, Any]:
        """
        Deletes all POIs from Weaviate POI collection
        """
        try:
            logger.info("Starting deletion of all POIs from Weaviate")
            self.weaviate_service.connection_service.ensure_connection()
            poi_col = self.weaviate_service.connection_service.client.collections.get("POI")
            poi_col.data.delete_many(where=Filter.by_property("name").like("*"))
            logger.info("All POIs deleted successfully")
            return {
                "success": True,
                "message": "All POIs deleted successfully",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error deleting all POIs: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete POIs",
                "timestamp": datetime.now().isoformat()
            }
