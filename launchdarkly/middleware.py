

"""Register request tracking middleware."""
import time
from flask import Blueprint, g, request, Flask
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)


def register_track_errors(target: Blueprint | Flask):
    """Register error tracking handlers that don't interfere with user handlers."""
    
    def track_error_on_teardown(error):
        """Track errors during request teardown."""
        if error is not None:
            try:
                # Determine status code (handle both HTTPException and regular exceptions)
                if isinstance(error, HTTPException):
                    status_code = error.code
                    error_type = error.__class__.__name__
                    error_message = str(error.description)
                else:
                    status_code = 500
                    error_type = error.__class__.__name__
                    error_message = str(error)
                
                # Track the error event
                from launchdarkly import track
                track(
                    "flask.error",
                    data={
                        "status_code": status_code,
                        "error_type": error_type,
                        "error_message": error_message,
                        "route": request.url_rule.rule if request.url_rule else request.path,
                        "method": request.method
                    }
                )
            except Exception as e:
                # Never let tracking errors break the app
                logger.exception(f"Error tracking failed: {e}")
    
    target.teardown_request(track_error_on_teardown)


def register_track_request_duration(target: Blueprint | Flask):
    target.before_request(_record_request_start)
    target.after_request(_track_request_duration)





def _record_request_start():
    """Track request start time."""
    g._ld_start_time = time.perf_counter()


def _track_request_duration(response):
    """Track request duration after each successful request."""
    try:
        if hasattr(g, '_ld_start_time'):
            duration_ms = (time.perf_counter() - g._ld_start_time) * 1000
            # Track the request duration event
            from launchdarkly import track
            track(
                "flask.response_time",
                data={
                    "status_code": response.status_code,
                    "route": request.url_rule.rule if request.url_rule else None,
                    "method": request.method
                },
                metric_value=duration_ms
            )
    except Exception as e:
        logger.exception(f"Error tracking request duration: {e}")
    return response

