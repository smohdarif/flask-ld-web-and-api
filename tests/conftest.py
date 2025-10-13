"""
Pytest configuration and fixtures for LaunchDarkly module tests.
"""
import pytest
import ldclient
from ldclient.config import Config
from ldclient.integrations.test_data import TestData
from flask import Flask
from launchdarkly import LaunchDarkly


@pytest.fixture(scope="session")
def test_data():
    """TestData instance for configuring flags during tests."""
    return TestData()


@pytest.fixture(scope="session")
def ld_client(test_data):
    """Configured LaunchDarkly client with TestData source and send_events=False."""
    config = Config(
        sdk_key="test-sdk-key",
        update_processor_class=test_data,
        send_events=False,  # Disable event sending for tests
        offline=False  # Keep online but use TestData
    )
    ldclient.set_config(config)
    client = ldclient.get()
    yield client
    client.close()


@pytest.fixture
def flask_app():
    """Flask application instance for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def ld_extension(ld_client, flask_app):
    """LaunchDarkly extension configured with test client."""
    extension = LaunchDarkly(ld_client, flask_app)
    return extension


@pytest.fixture
def test_client(flask_app):
    """Flask test client."""
    return flask_app.test_client()


@pytest.fixture
def app_context(flask_app):
    """Flask application context."""
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def request_context(flask_app):
    """Flask request context."""
    with flask_app.test_request_context():
        yield flask_app
