"""
Tests for the LaunchDarkly Flask extension core functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, g, has_request_context
from ldclient import Context

from launchdarkly import LaunchDarkly, variation, track, get_current_app_extension


class TestLaunchDarklyExtension:
    """Test the LaunchDarkly Flask extension class."""

    def test_init_without_app(self, ld_client):
        """Test initialization without Flask app."""
        extension = LaunchDarkly(ld_client)
        assert extension._client == ld_client
        assert extension.app is None
        assert extension._auto_track_duration is True
        assert extension._auto_track_errors is True

    def test_init_with_app(self, ld_client, flask_app):
        """Test initialization with Flask app."""
        extension = LaunchDarkly(ld_client, flask_app)
        assert extension._client == ld_client
        assert extension.app == flask_app
        assert 'launchdarkly' in flask_app.extensions

    def test_init_with_custom_options(self, ld_client):
        """Test initialization with custom tracking options."""
        extension = LaunchDarkly(
            ld_client, 
            auto_track_duration=False, 
            auto_track_errors=False
        )
        assert extension._auto_track_duration is False
        assert extension._auto_track_errors is False

    def test_init_app(self, ld_client, flask_app):
        """Test init_app method."""
        extension = LaunchDarkly(ld_client)
        extension.init_app(flask_app)
        
        assert extension.app == flask_app
        assert 'launchdarkly' in flask_app.extensions
        assert flask_app.extensions['launchdarkly'] == extension

    def test_get_client(self, ld_client, flask_app):
        """Test get_client method."""
        extension = LaunchDarkly(ld_client, flask_app)
        assert extension.get_client() == ld_client

    def test_get_client_not_initialized(self):
        """Test get_client when client is None."""
        extension = LaunchDarkly(None)
        with pytest.raises(RuntimeError, match="LaunchDarkly client not initialized"):
            extension.get_client()

    def test_shutdown(self, ld_client, flask_app):
        """Test shutdown method."""
        extension = LaunchDarkly(ld_client, flask_app)
        # Mock the client methods
        extension._client.flush = MagicMock()
        extension._client.close = MagicMock()
        
        extension.shutdown()
        
        extension._client.flush.assert_called_once()
        extension._client.close.assert_called_once()

    def test_shutdown_with_none_client(self):
        """Test shutdown when client is None."""
        extension = LaunchDarkly(None)
        # Should not raise an exception
        extension.shutdown()


class TestVariationMethod:
    """Test the variation method with various scenarios."""

    def test_variation_with_context(self, ld_client, flask_app, test_data, request_context):
        """Test variation method with proper context."""
        # Set up flag in TestData
        test_data.update(test_data.flag("test-flag").variation_for_all(True))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context in Flask g
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        result = extension.variation("test-flag", default=False)
        assert result is True

    def test_variation_without_request_context(self, ld_client, flask_app, test_data):
        """Test variation method outside request context."""
        test_data.update(test_data.flag("test-flag").variation_for_all(True))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Not in request context
        result = extension.variation("test-flag", default=False)
        assert result is False

    def test_variation_without_ld_context(self, ld_client, flask_app, test_data, request_context):
        """Test variation method without LD context set."""
        test_data.update(test_data.flag("test-flag").variation_for_all(True))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # No context in g.ld_context
        result = extension.variation("test-flag", default=False)
        assert result is False

    def test_variation_with_exception(self, ld_client, flask_app, request_context):
        """Test variation method when flag evaluation raises exception."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.variation to raise exception
        original_variation = extension._client.variation
        extension._client.variation = MagicMock(side_effect=Exception("Test error"))
        
        result = extension.variation("test-flag", default="fallback")
        assert result == "fallback"
        
        # Restore original method
        extension._client.variation = original_variation


class TestTrackMethod:
    """Test the track method with various scenarios."""

    def test_track_with_context(self, ld_client, flask_app, request_context):
        """Test track method with proper context."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        extension.track("test-event", data={"key": "value"}, metric_value=1.5)
        
        extension._client.track.assert_called_once_with(
            "test-event", 
            context, 
            data={"key": "value"}, 
            metric_value=1.5
        )

    def test_track_without_request_context(self, ld_client, flask_app):
        """Test track method outside request context."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        extension.track("test-event")
        
        # Should not call client.track
        extension._client.track.assert_not_called()

    def test_track_without_ld_context(self, ld_client, flask_app, request_context):
        """Test track method without LD context set."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        extension.track("test-event")
        
        # Should not call client.track
        extension._client.track.assert_not_called()

    def test_track_with_exception(self, ld_client, flask_app, request_context):
        """Test track method when tracking raises exception."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track to raise exception
        original_track = extension._client.track
        extension._client.track = MagicMock(side_effect=Exception("Test error"))
        
        # Should not raise exception
        extension.track("test-event")
        
        # Restore original method
        extension._client.track = original_track


class TestModuleLevelFunctions:
    """Test module-level helper functions."""

    def test_get_current_app_extension(self, ld_client, flask_app):
        """Test get_current_app_extension function."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        with flask_app.app_context():
            result = get_current_app_extension()
            assert result == extension

    def test_get_current_app_extension_no_extension(self, flask_app):
        """Test get_current_app_extension when no extension is registered."""
        with flask_app.app_context():
            result = get_current_app_extension()
            assert result is None

    def test_variation_helper_function(self, ld_client, flask_app, test_data, request_context):
        """Test module-level variation function."""
        test_data.update(test_data.flag("helper-flag").value_for_all(True))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Ensure we're using the real client, not a mock
        extension._client = ld_client
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        result = variation("helper-flag", default=False)
        assert result is True

    def test_variation_helper_no_extension(self, flask_app, request_context):
        """Test module-level variation function when no extension is registered."""
        result = variation("helper-flag", default="fallback")
        assert result == "fallback"

    def test_track_helper_function(self, ld_client, flask_app, request_context):
        """Test module-level track function."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        track("helper-event", data={"test": True})
        
        extension._client.track.assert_called_once_with(
            "helper-event", 
            context, 
            data={"test": True}, 
            metric_value=None
        )

    def test_track_helper_no_extension(self, flask_app, request_context):
        """Test module-level track function when no extension is registered."""
        # Should not raise exception
        track("helper-event")
