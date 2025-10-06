"""
Tracking middleware for monitoring request duration and errors.
Uses LaunchDarkly's track() method to send events.
"""
import time
from flask import request, g

from launchdarkly import get_client


def register_tracking_middleware(app):
    """
    Register tracking middleware with the Flask app.
    
    Args:
        app: Flask application instance
    """
    ld_client = get_client()
    
    @app.after_request
    def track_request_duration(response):
        """
        Track request duration after each successful request.
        """
        if hasattr(g, 'request_start_time') and hasattr(g, 'ld_request_context'):
            duration_ms = (time.time() - g.request_start_time) * 1000
            
            # Track the request duration event
            ld_client.track(
                "request_completed",
                g.ld_request_context,
                data={
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                    "route": request.url_rule.rule if request.url_rule else None,
                    "method": request.method
                },
                metric_value=duration_ms
            )
        
        return response
    
    @app.errorhandler(Exception)
    def track_request_error(error):
        """
        Track request errors with LaunchDarkly.
        """
        if hasattr(g, 'request_start_time') and hasattr(g, 'ld_request_context'):
            duration_ms = (time.time() - g.request_start_time) * 1000
            
            # Track the error event
            ld_client.track(
                "request_error",
                g.ld_request_context,
                data={
                    "duration_ms": duration_ms,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "route": request.url_rule.rule if request.url_rule else None,
                    "method": request.method
                },
                metric_value=duration_ms
            )
        
        # Re-raise the error to let Flask handle it normally
        raise
