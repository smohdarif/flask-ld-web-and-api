"""
LaunchDarkly Flask Extension.

A Flask extension for integrating LaunchDarkly feature flags with Flask applications.
Provides idiomatic Flask patterns for context management and flag evaluation.
"""
import atexit
import logging
import os
from typing import Optional, Dict, Any, Callable, List

import ldclient
from ldclient import Context
from ldclient.impl import AnyNum
from flask import Flask, g, request, has_request_context, current_app
from werkzeug.local import LocalProxy

from launchdarkly.middleware import register_track_request_duration, register_track_errors
from launchdarkly.contexts import get_context


logger = logging.getLogger(__name__)

LD_LOG_LEVEL = os.getenv("LD_LOG_LEVEL", "INFO").upper()

current_client = LocalProxy(lambda: _get_current_client())

__all__ = [
    'LaunchDarkly',
    'variation',
    'track',
    'current_client',
] 

def _get_current_client():
    if has_request_context():
        if current_app.extensions.get('launchdarkly'):
            return current_app.extensions['launchdarkly'].get_client()
    return None

class LaunchDarkly:
    """
    Flask extension for LaunchDarkly feature flags.
    
    Provides idiomatic Flask patterns for context management and flag evaluation.
    """
    
    def __init__(self, ldclient: ldclient.LDClient, app: Optional[Flask] = None, auto_track_duration: bool = True, auto_track_errors: bool = True):
        """
        Initialize the LaunchDarkly extension.
        
        Args:
            ldclient: LaunchDarkly client instance
            app: Flask application instance (optional)
            auto_track_duration: Whether to automatically track request duration (default: True)
            auto_track_errors: Whether to automatically track errors (default: True)
        """
        self.app = None
        self._client = ldclient
        self._auto_track_duration = auto_track_duration
        self._auto_track_errors = auto_track_errors
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Configure the extension for a Flask application.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Store extension in app.extensions per Flask convention
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['launchdarkly'] = self
      
        if self._auto_track_duration:
            register_track_request_duration(self.app)
        
        if self._auto_track_errors:
            register_track_errors(self.app)
        
        # Register Jinja2 template helpers
        app.jinja_env.globals['ld_variation'] = self.variation
        app.jinja_env.globals['ld_context'] = lambda: get_context()
    
    def get_client(self):
        """Get the LaunchDarkly client."""
        if self._client is None:
            raise RuntimeError("LaunchDarkly client not initialized. Call init_app() first.")
        return self._client
    
    def variation(self, flag_key: str, default=False) -> Any:
        """
        Evaluate a feature flag using the current request context.
        
        Args:
            flag_key: The LaunchDarkly flag key
            default: Default value if flag evaluation fails
            
        Returns:
            The flag variation value (type matches the flag's configured type)
            
        Example:
            # Boolean flag
            show_banner = ld.variation("show-banner", default=False)
            
            # String flag
            theme = ld.variation("theme", default="light")
            
            # Number flag
            max_items = ld.variation("max-items", default=10)
        """
        try:
            if not has_request_context():
                logger.warning(f"Variation called outside of request context for flag '{flag_key}'. Use ldclient.variation outside of a request context.")
                return default
            context = getattr(g, 'ld_context', None)
            if context is None:
                logger.warning(f"No LaunchDarkly context available for flag '{flag_key}'. Call add_context or replace_context before using variation. Using default value.", extra={"flag_key": flag_key, "path": request.path if has_request_context() else None})
                return default
            
            return self._client.variation(flag_key, context, default=default)
        except Exception as e:
            logger.warning(f"Flag evaluation failed for '{flag_key}': {e}", exc_info=True, extra={"flag_key": flag_key, "path": request.path if has_request_context() else None})
            return default
    
    def track(self, event_name: str, data: Optional[Any] = None, metric_value: Optional[AnyNum] = None) -> None:
        """
        Track an event using the current request context.
        
        Args:
            event_name: The event name to track
            data: Custom data dictionary to track with the event
            metric_value: Numeric metric value to track
            
        Returns:
            None
            
        Example:
            # Simple event tracking
            ld.track("user-login")
            
            # Event with custom data
            ld.track("purchase", data={"product": "widget", "price": 29.99})
            
            # Event with metric value
            ld.track("api-response-time", metric_value=150.5)
        """
        try:
            if not has_request_context():
                logger.warning(f"Track called outside of request context for event '{event_name}'. Use ldclient.track outside of a request context.")
                return
            context = getattr(g, 'ld_context', None)
            if context is None:
                logger.warning(f"No LaunchDarkly context available for event '{event_name}'. Call add_context or replace_context before using track. Skipping event.", extra={"event_name": event_name, "path": request.path if has_request_context() else None})
                return
            return self._client.track(event_name, context, data=data, metric_value=metric_value)
        except Exception as e:
            logger.warning(f"Error tracking event '{event_name}': {e}", extra={"event_name": event_name, "path": request.path if has_request_context() else None})
            return
    def shutdown(self) -> None:
        """Shutdown the LaunchDarkly client."""
        try:
            if self._client:
                self._client.flush()
                self._client.close()
        except Exception as e:
            logger.exception(f"Error during LaunchDarkly shutdown: {e}")


def get_current_app_extension() -> LaunchDarkly | None:
    """
    Get the LaunchDarkly extension from the current app.
    
    Returns:
        LaunchDarkly extension instance or None if not found
    """
    
    return current_app.extensions.get('launchdarkly')


def variation(flag_key: str, default: Any = False) -> Any:
    """
    Evaluate a feature flag using the current request context.
    
    This is a convenience function that uses the current app's LaunchDarkly extension.
    
    Args:
        flag_key: The LaunchDarkly flag key
        default: Default value if flag evaluation fails
    
    Returns:
        The flag variation value (type matches the flag's configured type)
        
    Example:
        from launchdarkly import variation
        
        # In a route handler
        @app.route('/dashboard')
        def dashboard():
            show_beta = variation('show-beta-features', default=False)
            return render_template('dashboard.html', beta=show_beta)
    """
    extension = get_current_app_extension()
    if extension is None:
        logger.warning(f"No LaunchDarkly extension found for flag '{flag_key}', returning default")
        return default
    return extension.variation(flag_key, default=default)


def track(event_name: str, data: Optional[Any] = None, metric_value: Optional[AnyNum] = None) -> None:
    """
    Track an event using the current request context.
    
    This is a convenience function that uses the current app's LaunchDarkly extension.
    
    Args:
        event_name: The event name to track
        data: Custom data dictionary to track with the event
        metric_value: Numeric metric value to track
        
    Returns:
        None
        
    Example:
        from launchdarkly import track
        
        # In a route handler
        @app.route('/api/data')
        def get_data():
            track('api-call', data={'endpoint': 'data'})
            return jsonify({'data': 'value'})
    """
    extension = get_current_app_extension()
    if extension is None:
        logger.warning(f"No LaunchDarkly extension found for event '{event_name}', skipping tracking")
        return
    return extension.track(event_name, data=data, metric_value=metric_value)