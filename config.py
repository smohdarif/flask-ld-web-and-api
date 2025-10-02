"""Flask configuration using Flask-idiomatic patterns."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    # LaunchDarkly
    LAUNCHDARKLY_SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
    LD_FLAG_KEY_WEB_BANNER = os.getenv("LD_FLAG_KEY_WEB_BANNER", "web-banner")
    
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    @staticmethod
    def validate():
        """Validate required configuration."""
        if not Config.LAUNCHDARKLY_SDK_KEY:
            raise RuntimeError(
                "LAUNCHDARKLY_SDK_KEY must be set in environment or .env file"
            )


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    LAUNCHDARKLY_SDK_KEY = "test-sdk-key"


# Config dictionary for easy selection
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": ProductionConfig
} 