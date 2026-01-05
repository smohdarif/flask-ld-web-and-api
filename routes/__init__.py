"""
Route registration for the Flask application.
Provides a central place to register all blueprints.
"""
from routes.web import web_bp
from routes.api import api_bp


def register_routes(app):
    """
    Register all route blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
