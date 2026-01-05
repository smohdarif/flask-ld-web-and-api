"""
Web routes for server-side rendered pages.
"""
from flask import Blueprint, render_template

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def home():
    """Home page showcasing LaunchDarkly Flask integration and Jinja2 template helpers."""
    return render_template("demo.html")


@web_bp.get("/health")
def health():
    """Health check endpoint for load balancers."""
    return "ok", 200
