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
import logging
import logging.config
import atexit
import os
from flask import Flask
from ldclient.config import Config as LDConfig
import ldclient
from launchdarkly import LaunchDarkly

from launchdarkly.contexts import add_context, create_request_context
from flask import request
from dotenv import load_dotenv
from routes import register_routes
from config import get_logging_config
load_dotenv()
# Create Flask application
app = Flask(__name__)

# use FLASK__LAUCHDARKLY__SDK_KEY to set the SDK key
app.config.setdefault("LAUNCHDARKLY", {})
app.config.from_prefixed_env(prefix="FLASK_")
logging.config.dictConfig(get_logging_config(app.config))
ldconfig = app.config.get("LAUNCHDARKLY")
ldclient.set_config(LDConfig(
    sdk_key=ldconfig.get("SDK_KEY"),
    send_events=ldconfig.get("SEND_EVENTS", True),
    offline=ldconfig.get("OFFLINE", False),
    all_attributes_private=ldconfig.get("ALL_ATTRIBUTES_PRIVATE", False),
    # avoid sending high cardinality contexts such as requests or sessions in index/identify events
    omit_anonymous_contexts=ldconfig.get("OMIT_ANONYMOUS_CONTEXTS", True),
    # allow overriding all uris with a single environment variable ENDPOINT_URI
    base_uri=ldconfig.get("BASE_URI", ldconfig.get("ENDPOINT_URI", "https://app.launchdarkly.com")),
    events_uri=ldconfig.get("EVENTS_URI", ldconfig.get("ENDPOINT_URI", "https://events.launchdarkly.com")),
    stream_uri=ldconfig.get("STREAM_URI", ldconfig.get("ENDPOINT_URI", "https://stream.launchdarkly.com")),
    application = {
        "name": "Flask Demo",
        "version": "1.0.0"
    }
))
# log the config for debug
ld = LaunchDarkly(ldclient.get(), app)

# Add contexts to the request
@app.before_request
def build_request_context():
    add_context(create_request_context())



# Register routes (web pages, API endpoints)
register_routes(app)