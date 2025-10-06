"""
Middleware registration for the Flask application.
Provides a central place to register all middleware.
"""
from middleware.context import register_context_middleware
from middleware.tracking import register_tracking_middleware


def register_middleware(app):
    """
    Register all middleware with the Flask application.
    
    Args:
        app: Flask application instance
    """
    register_context_middleware(app)
    register_tracking_middleware(app)
