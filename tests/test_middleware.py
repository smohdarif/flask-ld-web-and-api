"""
Tests for LaunchDarkly middleware functions.
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from flask import Flask, g, request, Response
from werkzeug.exceptions import HTTPException, NotFound

from launchdarkly.middleware import (
    register_track_request_duration,
    register_track_errors,
    _record_request_start,
    _track_request_duration
)
from launchdarkly import LaunchDarkly


class TestRegisterTrackRequestDuration:
    """Test register_track_request_duration function."""

    def test_register_track_request_duration_with_flask_app(self, ld_client, flask_app, request_context):
        """Test registering request duration tracking with Flask app."""
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        # Mock the track function
        with patch('launchdarkly.track') as mock_track:
            # Make a request with a proper route
            @flask_app.route('/test')
            def test_route():
                pass
                
            with flask_app.test_request_context('/test', method='GET'):
                # Simulate request processing
                g._ld_start_time = time.perf_counter()
                time.sleep(0.001)  # Small delay to ensure measurable duration
                
                # Create a mock response
                response = Response("test response", status=200)
                
                # Call the tracking function
                _track_request_duration(response)
                
                # Verify track was called
                mock_track.assert_called_once()
                call_args = mock_track.call_args
                assert call_args[0][0] == "flask.response_time"
                assert call_args[1]["data"]["status_code"] == 200
                assert call_args[1]["data"]["route"] == "/test"
                assert call_args[1]["data"]["method"] == "GET"
                assert call_args[1]["metric_value"] > 0  # Should have positive duration

    def test_register_track_request_duration_with_blueprint(self, ld_client, flask_app):
        """Test registering request duration tracking with Blueprint."""
        from flask import Blueprint
        
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        bp = Blueprint('test', __name__)
        
        # Mock the track function
        with patch('launchdarkly.track') as mock_track:
            register_track_request_duration(bp)
            
            # Verify before_request and after_request were registered
            assert len(bp.before_request_funcs[None]) > 0
            assert len(bp.after_request_funcs[None]) > 0

    def test_record_request_start(self, flask_app, request_context):
        """Test _record_request_start function."""
        with flask_app.test_request_context():
            _record_request_start()
            assert hasattr(g, '_ld_start_time')
            assert isinstance(g._ld_start_time, float)

    def test_track_request_duration_no_start_time(self, ld_client, flask_app, request_context):
        """Test _track_request_duration when no start time is recorded."""
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track') as mock_track:
            with flask_app.test_request_context():
                # No start time recorded
                response = Response("test response", status=200)
                _track_request_duration(response)
                
                # Should not call track
                mock_track.assert_not_called()

    def test_track_request_duration_with_exception(self, ld_client, flask_app, request_context):
        """Test _track_request_duration when tracking raises exception."""
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track', side_effect=Exception("Tracking error")):
            with flask_app.test_request_context():
                g._ld_start_time = time.perf_counter()
                response = Response("test response", status=200)
                
                # Should not raise exception
                result = _track_request_duration(response)
                assert result == response


class TestRegisterTrackErrors:
    """Test register_track_errors function."""

    def test_register_track_errors_with_flask_app(self, ld_client, flask_app):
        """Test registering error tracking with Flask app."""
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track') as mock_track:
            register_track_errors(flask_app)
            
            # Verify teardown handler was registered (check that we have teardown functions)
            assert len(flask_app.teardown_request_funcs) > 0

    def test_register_track_errors_with_blueprint(self, ld_client, flask_app):
        """Test registering error tracking with Blueprint."""
        from flask import Blueprint
        
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        bp = Blueprint('test', __name__)
        
        with patch('launchdarkly.track') as mock_track:
            register_track_errors(bp)
            
            # Verify teardown handler was registered (check that we have teardown functions)
            assert len(bp.teardown_request_funcs) > 0

    def test_error_tracking_http_exception(self, ld_client, flask_app, test_client):
        """Test error tracking for HTTPException."""
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track') as mock_track:
            register_track_errors(flask_app)
            
            @flask_app.route('/test-404')
            def test_route():
                raise NotFound("Page not found")
            
            # Make request that will trigger 404
            response = test_client.get('/test-404')
            assert response.status_code == 404
            
            # HTTPExceptions are handled by Flask internally and don't trigger error tracking
            # No tracking should be called since auto_track_duration=False
            mock_track.assert_not_called()

    def test_error_tracking_generic_exception(self, ld_client, flask_app, test_client):
        """Test error tracking for generic Exception."""
        # Disable testing mode to allow proper exception handling
        flask_app.config['TESTING'] = False
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track') as mock_track:
            register_track_errors(flask_app)
            
            @flask_app.route('/test-error')
            def test_route():
                raise ValueError("Something went wrong")
            
            # Make request that will trigger error
            response = test_client.get('/test-error')
            assert response.status_code == 500
            
            # Verify only error tracking was called (no response time tracking)
            mock_track.assert_called_once()
            call_args = mock_track.call_args
            assert call_args[0][0] == "flask.error"
            assert call_args[1]["data"]["status_code"] == 500
            assert call_args[1]["data"]["error_type"] == "ValueError"
            assert call_args[1]["data"]["error_message"] == "Something went wrong"
            assert call_args[1]["data"]["route"] == "/test-error"
            assert call_args[1]["data"]["method"] == "GET"

    def test_error_tracking_without_url_rule(self, ld_client, flask_app, test_client):
        """Test error tracking when request has no url_rule."""
        # Disable testing mode to allow proper exception handling
        flask_app.config['TESTING'] = False
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track') as mock_track:
            register_track_errors(flask_app)
            
            @flask_app.route('/test-no-rule')
            def test_route():
                # Mock request to have no url_rule
                request.url_rule = None
                raise ValueError("Error without rule")
            
            # Make request that will trigger error
            response = test_client.get('/test-no-rule')
            assert response.status_code == 500
            
            # Verify only error tracking was called (no response time tracking)
            mock_track.assert_called_once()
            call_args = mock_track.call_args
            assert call_args[0][0] == "flask.error"
            assert call_args[1]["data"]["route"] == "/test-no-rule"  # Falls back to request.path

    def test_error_tracking_propagation(self, ld_client, flask_app, test_client):
        """Test that error tracking doesn't interfere with user error handlers."""
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track') as mock_track:
            register_track_errors(flask_app)
            
            # Register user error handler
            @flask_app.errorhandler(ValueError)
            def handle_value_error(error):
                return "Custom error handler", 400
            
            @flask_app.route('/test-propagation')
            def test_route():
                raise ValueError("Test error")
            
            # Make request
            response = test_client.get('/test-propagation')
            
            # Verify user handler was called, but no tracking since user handler handles the exception
            assert response.status_code == 400
            assert response.data.decode() == "Custom error handler"
            mock_track.assert_not_called()

    def test_error_tracking_exception_in_tracking(self, ld_client, flask_app, test_client):
        """Test error tracking when tracking itself raises exception."""
        # Disable testing mode to allow proper exception handling
        flask_app.config['TESTING'] = False
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track', side_effect=Exception("Tracking failed")):
            register_track_errors(flask_app)
            
            @flask_app.route('/test-tracking-error')
            def test_route():
                raise ValueError("Original error")
            
            # Should not raise exception, should propagate original error
            response = test_client.get('/test-tracking-error')
            assert response.status_code == 500


class TestMiddlewareIntegration:
    """Test middleware integration scenarios."""

    def test_both_middleware_registered(self, ld_client, flask_app):
        """Test registering both request duration and error tracking."""
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        with patch('launchdarkly.track') as mock_track:
            register_track_request_duration(flask_app)
            register_track_errors(flask_app)
            
            @flask_app.route('/test-both')
            def test_route():
                return "Success", 200
            
            # Make successful request
            response = flask_app.test_client().get('/test-both')
            
            # Should track request duration
            assert response.status_code == 200
            # Verify track was called for request duration
            mock_track.assert_called()
            call_args = mock_track.call_args
            assert call_args[0][0] == "flask.response_time"

    def test_middleware_with_auto_tracking_disabled(self, ld_client, flask_app):
        """Test middleware when auto tracking is disabled."""
        extension = LaunchDarkly(ld_client, flask_app, auto_track_duration=False, auto_track_errors=False)
        
        # Should not register any middleware
        assert len(flask_app.before_request_funcs[None]) == 0
        assert len(flask_app.after_request_funcs[None]) == 0
        assert Exception not in flask_app.error_handler_spec[None]
