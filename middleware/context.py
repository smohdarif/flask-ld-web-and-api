"""
Context middleware for building LaunchDarkly contexts.
Builds user and request contexts before each request.
"""
import time
from flask import request, g

from launchdarkly.contexts import user_to_ld_context, request_to_ld_context


def register_context_middleware(app):
    """
    Register context-building middleware with the Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def build_contexts():
        """
        Build LaunchDarkly contexts from request and store in Flask's g object.
        Also track request start time for duration tracking.
        """
        # Store request start time for duration tracking
        g.request_start_time = time.time()
        
        # Check if user is provided in query params, otherwise use default
        user_key = request.args.get("user", "web-visitor")
        
        # Build user context with user key; in real apps, add more attributes
        # like email, custom attributes, etc.
        g.ld_context = user_to_ld_context(user_key)
        
        # Also build a request context for tracking (always uses 'x_ld_request' kind)
        g.ld_request_context = request_to_ld_context(request)
