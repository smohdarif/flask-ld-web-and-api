"""
Flask + LaunchDarkly Web & API Demo
Flask-idiomatic function-based implementation.

This version demonstrates Flask best practices:
- Application factory pattern
- Flask config object for configuration
- Helper functions instead of direct SDK access
- Non-blocking LaunchDarkly initialization
- Proper use of Flask's g and current_app
"""
from flask import Flask, jsonify, render_template, request
from ldclient import Context

# Import our Flask-idiomatic helpers
from launchdarkly_helpers import (
    init_launchdarkly,
    evaluate_flag,
    build_context_from_request,
    get_ld_client
)
from config import config


def create_app(config_name='production'):
    """
    Application factory function (Flask best practice).
    
    Args:
        config_name: Configuration name ('development', 'production', 'testing')
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration using Flask config pattern
    app.config.from_object(config[config_name])
    
    # Validate configuration
    config[config_name].validate()
    
    # Initialize LaunchDarkly using helper function
    init_launchdarkly(app)
    
    # Register routes
    register_routes(app)
    
    return app


def register_routes(app):
    """Register all application routes."""
    
    @app.get("/")
    def home():
        """Server-side rendered page with flag-controlled banner."""
        flag_key = app.config.get('LD_FLAG_KEY_WEB_BANNER', 'web-banner')
        
        # Build context for this request
        ctx = Context.builder("web-visitor").build()
        
        # Evaluate flag using helper function
        banner_on = evaluate_flag(flag_key, ctx, default=False)
        
        return render_template("index.html", banner_on=banner_on, flag_key=flag_key)
    
    @app.get("/api/flag/<flag_key>")
    def read_flag(flag_key):
        """JSON API to evaluate any flag for a given user (?user=key)."""
        # Build context from request using helper
        ctx = build_context_from_request(request, default_key="anon")
        
        # Evaluate flag
        value = evaluate_flag(flag_key, ctx, default=False)
        
        # Extract user key for response
        user_key = request.args.get("user", "anon")
        
        return jsonify({
            "flag": flag_key,
            "user": user_key,
            "value": value
        })
    
    @app.get("/health")
    def health():
        """Health check endpoint for load balancers."""
        return "ok", 200
    
    @app.get("/status")
    def status():
        """LaunchDarkly connection status endpoint."""
        client = get_ld_client()
        initialized = client.is_initialized() if client else False
        
        return jsonify({
            "launchdarkly_initialized": initialized,
            "status": "ready" if initialized else "initializing"
        })


# Create app instance using factory pattern
# For Gunicorn: gunicorn "app_idiomatic:create_app()" --config gunicorn.conf.py
app = create_app()


if __name__ == "__main__":
    # For development: python app_idiomatic.py
    app = create_app('development')
    app.run(debug=True) 