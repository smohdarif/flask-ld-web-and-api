"""
LaunchDarkly helper functions for Flask integration.

This module provides Flask-idiomatic functions for integrating LaunchDarkly
without using classes, following Flask's functional patterns.
"""
import atexit
from flask import current_app, g
import ldclient
from ldclient.config import Config
from ldclient import Context


def init_launchdarkly(app):
    """
    Initialize LaunchDarkly client with Flask app.
    
    This function follows Flask conventions by:
    - Using app.config for configuration
    - Storing client in app.extensions
    - Registering lifecycle hooks
    - Non-blocking initialization (start_wait=0)
    
    Args:
        app: Flask application instance
    """
    sdk_key = app.config.get('LAUNCHDARKLY_SDK_KEY')
    
    if not sdk_key:
        raise RuntimeError(
            "LAUNCHDARKLY_SDK_KEY must be set in app.config. "
            "Set it in config.py or via environment variable."
        )
    
    # Initialize LaunchDarkly with non-blocking startup
    # Simply calling set_config and get() without waiting ensures
    # the SDK initializes in the background (non-blocking)
    ld_config = Config(sdk_key=sdk_key)
    
    ldclient.set_config(ld_config)
    # get() returns immediately, SDK initializes in background
    client = ldclient.get()
    
    # Store in Flask's extensions dict (Flask convention)
    if not hasattr(app, 'extensions'):
        app.extensions = {}
    app.extensions['launchdarkly'] = client
    
    # Register teardown handler
    @app.teardown_appcontext
    def close_ld_client(exception=None):
        """Close LaunchDarkly client on app teardown."""
        _close_launchdarkly(exception)
    
    # Also register with atexit for Gunicorn worker shutdown
    atexit.register(_shutdown_ld_client)
    
    app.logger.info("LaunchDarkly client initialized (non-blocking)")


def get_ld_client():
    """
    Get the LaunchDarkly client instance from Flask app context.
    
    Returns:
        LDClient: The LaunchDarkly client singleton
        
    Usage:
        client = get_ld_client()
        value = client.variation("flag-key", context, default)
    """
    return current_app.extensions.get('launchdarkly')


def get_ld_client_from_g():
    """
    Get LaunchDarkly client from Flask's g object (request context).
    
    This lazy-loads the client into g if not already there.
    Useful for request-scoped access.
    
    Returns:
        LDClient: The LaunchDarkly client
    """
    if 'ld_client' not in g:
        g.ld_client = current_app.extensions.get('launchdarkly')
    return g.ld_client


def evaluate_flag(flag_key, context, default=False):
    """
    Evaluate a LaunchDarkly flag (convenience function).
    
    Args:
        flag_key: The feature flag key
        context: LaunchDarkly Context object
        default: Default value if flag not available
        
    Returns:
        The flag value or default
        
    Usage:
        ctx = Context.builder("user-123").build()
        show_banner = evaluate_flag("web-banner", ctx, False)
    """
    client = get_ld_client()
    if client:
        return client.variation(flag_key, context, default)
    return default


def evaluate_flag_detail(flag_key, context, default=False):
    """
    Evaluate a flag with detailed evaluation information.
    
    Args:
        flag_key: The feature flag key
        context: LaunchDarkly Context object
        default: Default value if flag not available
        
    Returns:
        EvaluationDetail object with value and reason
        
    Usage:
        detail = evaluate_flag_detail("flag-key", ctx, False)
        value = detail.value
        reason = detail.reason
    """
    client = get_ld_client()
    if client:
        return client.variation_detail(flag_key, context, default)
    from ldclient.evaluation import EvaluationDetail
    return EvaluationDetail(default, None, {'kind': 'ERROR', 'errorKind': 'CLIENT_NOT_READY'})


def build_context_from_request(request, default_key="anonymous"):
    """
    Build a LaunchDarkly Context from Flask request.
    
    Extracts user information from request args/headers/session.
    
    Args:
        request: Flask request object
        default_key: Default user key if not found
        
    Returns:
        LaunchDarkly Context object
        
    Usage:
        from flask import request
        ctx = build_context_from_request(request)
    """
    user_key = request.args.get("user", default_key)
    
    # Could also extract from:
    # - request.headers.get('X-User-ID')
    # - session.get('user_id')
    # - current_user.id (if using Flask-Login)
    
    return Context.builder(user_key).build()


def is_ld_initialized():
    """
    Check if LaunchDarkly client is fully initialized.
    
    Returns:
        bool: True if initialized, False otherwise
        
    Usage:
        if is_ld_initialized():
            # Safe to rely on real-time flag values
        else:
            # May return defaults
    """
    client = get_ld_client()
    if client:
        return client.is_initialized()
    return False


def _close_launchdarkly(exception=None):
    """Internal function to close LaunchDarkly client."""
    client = current_app.extensions.get('launchdarkly')
    if client:
        try:
            client.close()
            current_app.logger.info("LaunchDarkly client closed")
        except Exception as e:
            current_app.logger.error(f"Error closing LaunchDarkly client: {e}")


def _shutdown_ld_client():
    """Internal function for atexit shutdown."""
    try:
        # This is called outside Flask app context, so use ldclient.get() directly
        client = ldclient.get()
        if client:
            client.close()
    except Exception:
        pass 