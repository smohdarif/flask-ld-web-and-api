"""
LaunchDarkly client initialization and management.
This module handles the singleton client instance and lifecycle.
"""
import atexit
from ldclient.config import Config as LDConfig
import ldclient

from config import Config

# ---------------------------
# Initialize LD client BEFORE forking (works best with Gunicorn --preload)
# ---------------------------
Config.validate()
ldclient.set_config(LDConfig(Config.LAUNCHDARKLY_SDK_KEY))
ld_client = ldclient.get()


# Ensure clean shutdown
@atexit.register
def _close_ld():
    """Close LaunchDarkly client on application shutdown."""
    try:
        ld_client.close()
    except Exception:
        pass


def get_client():
    """
    Get the LaunchDarkly client singleton instance.
    
    Returns:
        The LaunchDarkly client instance
    """
    return ld_client
