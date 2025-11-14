"""
API routes for REST endpoints.
"""
from flask import Blueprint, jsonify, request

from launchdarkly import variation

from launchdarkly.decorators import require_flag
from launchdarkly.contexts import get_context

api_bp = Blueprint("api", __name__)


@api_bp.get("/flag/<flag_key>")
def read_flag(flag_key):
    """
    Simple JSON API to evaluate any flag for a given user (?user=key).
    
    Args:
        flag_key: The LaunchDarkly flag key to evaluate
    
    Query Parameters:
        user: The user key for flag evaluation (default: "web-visitor")
    
    Returns:
        JSON response with flag key, user, and value
    """
    value = variation(flag_key, default=False)
    
    return jsonify({
        "flag": flag_key,
        "value": value,
        "context": get_context().to_dict() if get_context() else None
    })


@api_bp.get("/beta/experimental")
@require_flag("enable-experimental-api", default=False)
def experimental_feature():
    """
    Example of a feature-gated endpoint.
    
    This endpoint is only accessible when the 'enable-experimental-api' flag
    evaluates to True for the current user. Otherwise, returns 404.
    
    Query Parameters:
        user: The user key for flag evaluation (default: "web-visitor")
    
    Returns:
        JSON response with experimental data
    """
    return jsonify({
        "message": "Welcome to the experimental API!",
        "status": "beta",
        "features": ["feature-1", "feature-2", "feature-3"]
    })
