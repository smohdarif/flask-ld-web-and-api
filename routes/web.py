"""
Web routes for server-side rendered pages.
"""
from flask import Blueprint, render_template

from config import Config
from launchdarkly.flags import get_flag

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def home():
    """Server-side rendered page that uses a flag to toggle a banner."""
    flag_key = Config.LD_FLAG_KEY_WEB_BANNER
    banner_on = get_flag(flag_key, default=False)
    return render_template("index.html", banner_on=banner_on, flag_key=flag_key)


@web_bp.get("/health")
def health():
    """Health check endpoint for load balancers."""
    return "ok", 200
