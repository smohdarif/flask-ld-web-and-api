"""
LaunchDarkly decorators for route handlers.
Provides convenient decorators for feature-gating routes, context management, and request tracking.
"""
from functools import wraps
from typing import Callable, Optional, Any
from flask import abort, redirect, request, g
from ldclient import Context
from ldclient.impl import AnyNum
from launchdarkly.contexts import add_context
import logging

from launchdarkly import variation, track

logger = logging.getLogger(__name__)


def require_flag(flag_key: str, default: bool = False, expected_value: bool = True, redirect_url: Optional[str] = None) -> Callable:
    """
    Decorator that gates a route based on a feature flag value.
    
    If the flag evaluates to expected_value, the route handler executes normally.
    Otherwise, either redirects to redirect_url
    if provided, or returns 404 Not Found.
    
    This is useful for:
    - Gradually rolling out new endpoints
    - A/B testing different route implementations
    - Hiding routes from specific users or segments
    - Redirecting users to alternative pages when features are disabled
    
    Args:
        flag_key: The LaunchDarkly flag key to evaluate
        default: Default value if flag evaluation fails (default: False)
        expected_value: The value of the flag that will allow the route handler to execute (default: True)
        redirect_url: URL to redirect to if flag is False (optional)
    
    Returns:
        Decorator function
    
    Example:
        @app.get("/beta-feature")
        @require_flag("enable-beta-feature", default=False, expected_value=True, redirect_url="/coming-soon")
        def beta_feature():
            return "This is a beta feature!"
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Evaluate the flag using the user context from g.ld_context
            flag_value = variation(flag_key, default=default)
            
            # If flag is False, either redirect or return 404
            if flag_value != expected_value:
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    abort(404)
            
            # If flag is True, execute the route handler
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def with_context(context_fn: Callable[[], Context] | Context) -> Callable:
    """
    Decorator to add context for a specific route.
    
    Args:
        context_fn: Function that returns a LaunchDarkly Context
        
    Returns:
        Decorator function
    
    Example:
        @with_context(lambda: Context.builder('admin').kind('role').build())
        def admin_route():
            return "Admin only content"
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if callable(context_fn):
                context = context_fn()
            else:
                context = context_fn
            if context is not None:
                add_context(context)
            return view_func(*args, **kwargs)
        return wrapper
    return decorator



def track_after(event_name: str, data: Optional[Any] = None, metric_value: Optional[AnyNum] = None) -> Callable:
    """
    Decorator to track custom events for a specific route.
    
    Args:
        event_name: The event name to track
        data: Custom data dictionary to track with the event
        metric_value: Numeric metric value to track
    
    Returns:
        Decorator function
    
    Example:
        @track_after('user-action', data={'action': 'profile-view'}, metric_value=1)
        def view_profile():
            return render_template('profile.html')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            response = view_func(*args, **kwargs)
            track(event_name, data=data, metric_value=metric_value)
            return response
        return wrapper
    return decorator



def track_before(event_name: str, data: Optional[Any] = None, metric_value: Optional[AnyNum] = None) -> Callable:
    """
    Decorator to track custom events before a route executes.
    
    Args:
        event_name: The event name to track
        data: Custom data dictionary to track with the event
        metric_value: Numeric metric value to track
    
    Returns:
        Decorator function
    
    Example:
        @track_before('api-call', data={'endpoint': 'user-profile'})
        def get_user_profile():
            return jsonify({'user': 'data'})
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            track(event_name, data=data, metric_value=metric_value)
            response = view_func(*args, **kwargs)
            return response
        return wrapper
    return decorator


