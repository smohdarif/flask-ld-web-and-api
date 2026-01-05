"""
Configuration management for the Flask application.
Centralizes environment variable loading and validation.
"""
import os
from dotenv import load_dotenv
import logging
import logging.config

from flask import Config

# Load .env for local/dev
load_dotenv()


# Configure Flask logging using modern dict config approach
def get_logging_config(config: Config):
    """Configure Flask logging using dict config for better maintainability."""
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': 'app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            '': {  # Root logger
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'app': {  # Flask app logger
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'werkzeug': {  # Flask's WSGI server
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            },
            'ldclient': {  # LaunchDarkly client
                'level': config.get("LAUNCHDARKLY", {}).get("LOG_LEVEL", "DEBUG"),
                'handlers': ['console'],
                'propagate': False
            }
        }
    }
    
    # Apply the configuration
    return logging_config

