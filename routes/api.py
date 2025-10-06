"""
API routes for REST endpoints.
"""
from flask import Blueprint, jsonify, request

from launchdarkly.flags import get_flag
from launchdarkly.decorators import feature_gate

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
    value = get_flag(flag_key, default=False)
    user_key = request.args.get("user", "web-visitor")
    
    return jsonify({
        "flag": flag_key,
        "user": user_key,
        "value": value
    })


@api_bp.get("/beta/experimental")
@feature_gate("enable-experimental-api", fallback=False)
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
