"""
API routes package - Import all routers from individual route files
"""
from .chat import router as chat_router
from .properties import router as properties_router
from .conversations import router as conversations_router
from .analytics import router as analytics_router
from .sync import router as sync_router
from .cache import router as cache_router
from .health import router as health_router
from .deletion import router as deletion_router
from .enrichment import router as enrichment_router

__all__ = [
    'chat_router',
    'properties_router', 
    'conversations_router',
    'analytics_router',
    'sync_router',
    'cache_router',
    'health_router',
    'deletion_router',
    'enrichment_router'
]