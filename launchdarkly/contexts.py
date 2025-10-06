"""
LaunchDarkly context builders.
Functions to build LD contexts from various sources (users, requests, etc.).
"""
from uuid import uuid4
from ldclient import Context


def user_to_ld_context(user_key, **attributes):
    """
    Build a LaunchDarkly user context.
    
    Args:
        user_key: The user's unique identifier
        **attributes: Additional user attributes (email, name, custom fields, etc.)
    
    Returns:
        LaunchDarkly Context
    """
    builder = Context.builder(user_key)
    
    # Add any additional attributes
    for key, value in attributes.items():
        builder.set(key, value)
    
    return builder.build()


def request_to_ld_context(req):
    """
    Build a LaunchDarkly context from Flask request object.
    Similar to Node.js requestToLDContext pattern.
    
    Always uses 'x_ld_request' as the context kind, following LaunchDarkly
    conventions for custom context kinds.
    
    Args:
        req: Flask request object
    
    Returns:
        LaunchDarkly Context with kind 'x_ld_request'
    """
    # Get the matched route pattern if available
    route_path = None
    if req.url_rule:
        route_path = req.url_rule.rule
    
    return Context.builder(str(uuid4())) \
        .kind("x_ld_request") \
        .anonymous(True) \
        .set("route", route_path) \
        .set("method", req.method) \
        .set("baseUrl", req.base_url) \
        .set("ipAddress", req.remote_addr) \
        .set("hostname", req.host) \
        .build()
