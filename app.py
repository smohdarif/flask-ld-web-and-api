"""
Flask + LaunchDarkly: Web & API Demo

A production-ready Flask application demonstrating LaunchDarkly feature flag
integration with both server-side rendering and REST API endpoints.

This is the main application entry point that:
1. Initializes the Flask app
2. Registers middleware
3. Registers routes

The LaunchDarkly client is initialized in the launchdarkly package before
this module is loaded, ensuring proper singleton initialization before
Gunicorn forks workers.
"""
from flask import Flask

# Import to trigger LD client initialization (must happen before forking)
import launchdarkly  # noqa: F401

from middleware import register_middleware
from routes import register_routes

# Create Flask application
app = Flask(__name__)

# Register middleware (context building, tracking)
register_middleware(app)

# Register routes (web pages, API endpoints)
register_routes(app)