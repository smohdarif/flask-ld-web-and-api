import os
import atexit
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

# Load .env for local/dev
load_dotenv()

from ldclient.config import Config
from ldclient import Context
import ldclient

# ---------------------------
# 1) Initialize LD BEFORE forking (works best with Gunicorn --preload)
# ---------------------------
SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
if not SDK_KEY:
    raise RuntimeError("Set LAUNCHDARKLY_SDK_KEY in your environment or .env file.")

ldclient.set_config(Config(SDK_KEY))
ld = ldclient.get()

# Ensure clean shutdown
@atexit.register
def _close_ld():
    try:
        ld.close()
    except Exception:
        pass

app = Flask(__name__)

def user_context_from_request():
    # Very basic demo context; in real apps, include real user attributes.
    user_key = request.args.get("user", "anon")
    return Context.builder(user_key).build()

@app.get("/")
def home():
    """Server-side rendered page that uses a flag to toggle a banner."""
    flag_key = os.getenv("LD_FLAG_KEY_WEB_BANNER", "web-banner")
    ctx = Context.builder("web-visitor").build()
    banner_on = ld.variation(flag_key, ctx, default=False)
    return render_template("index.html", banner_on=banner_on, flag_key=flag_key)

@app.get("/api/flag/<flag_key>")
def read_flag(flag_key):
    """Simple JSON API to evaluate any flag for a given user (?user=key)."""
    ctx = user_context_from_request()
    value = ld.variation(flag_key, ctx, default=False)
    user_key = request.args.get("user", "anon")
    return jsonify({
        "flag": flag_key,
        "user": user_key,
        "value": value
    })

@app.get("/health")
def health():
    return "ok", 200
