"""
Configuration management for the Flask application.
Centralizes environment variable loading and validation.
"""
import os
from dotenv import load_dotenv

# Load .env for local/dev
load_dotenv()


class Config:
    """Application configuration."""
    
    # LaunchDarkly Configuration
    LAUNCHDARKLY_SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
    LD_FLAG_KEY_WEB_BANNER = os.getenv("LD_FLAG_KEY_WEB_BANNER", "web-banner")
    
    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        if not cls.LAUNCHDARKLY_SDK_KEY:
            raise RuntimeError(
                "Set LAUNCHDARKLY_SDK_KEY in your environment or .env file."
            )
