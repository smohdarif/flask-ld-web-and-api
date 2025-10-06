"""
LaunchDarkly decorators for route handlers.
Provides convenient decorators for feature-gating routes.
"""
from functools import wraps
from flask import abort

from launchdarkly.flags import get_flag


def feature_gate(flag_key, fallback=False):
    """
    Decorator that gates a route based on a feature flag value.
    
    If the flag evaluates to True, the route handler executes normally.
    If the flag evaluates to False (or fallback), returns 404 Not Found.
    
    This is useful for:
    - Gradually rolling out new endpoints
    - A/B testing different route implementations
    - Hiding routes from specific users or segments
    
    Args:
        flag_key: The LaunchDarkly flag key to evaluate
        fallback: Default value if flag evaluation fails (default: False)
    
    Returns:
        Decorator function
    
    Example:
        @app.get("/beta-feature")
        @feature_gate("enable-beta-feature", fallback=False)
        def beta_feature():
            return "This is a beta feature!"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Evaluate the flag using the user context from g.ld_context
            flag_value = get_flag(flag_key, default=fallback)
            
            # If flag is False, return 404
            if not flag_value:
                abort(404)
            
            # If flag is True, execute the route handler
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
