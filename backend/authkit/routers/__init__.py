from .auth import router
from .stats import router as stats_router
from .admin_stats import router as admin_stats_router
from .oauth import router as oauth_router

__all__ = ['router', 'stats_router', 'admin_stats_router', 'oauth_router']
