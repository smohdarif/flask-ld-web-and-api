"""
Tests for LaunchDarkly decorators.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, g, abort, redirect
from ldclient import Context

from launchdarkly.decorators import (
    require_flag,
    with_context,
    track_after,
    track_before
)
from launchdarkly import LaunchDarkly


class TestRequireFlagDecorator:
    """Test @require_flag decorator."""

    def test_require_flag_enabled(self, ld_client, flask_app, test_data, request_context):
        """Test @require_flag when flag is enabled."""
        # Set up flag in TestData
        test_data.update(test_data.flag("test-feature").variation_for_all(True))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        @require_flag("test-feature", default=False)
        def test_route():
            return "Feature enabled!"
        
        result = test_route()
        assert result == "Feature enabled!"

    def test_require_flag_disabled_default_behavior(self, ld_client, flask_app, test_data, request_context):
        """Test @require_flag when flag is disabled (default behavior - 404)."""
        # Set up flag in TestData
        test_data.update(test_data.flag("test-feature").variation_for_all(False))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        @require_flag("test-feature", default=False)
        def test_route():
            return "Feature enabled!"
        
        with pytest.raises(Exception):  # Flask's abort raises an exception
            test_route()

    def test_require_flag_disabled_with_redirect(self, ld_client, flask_app, test_data, request_context):
        """Test @require_flag when flag is disabled with redirect."""
        # Set up flag in TestData
        test_data.update(test_data.flag("test-feature").variation_for_all(False))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        @require_flag("test-feature", default=False, redirect_url="/coming-soon")
        def test_route():
            return "Feature enabled!"
        
        with flask_app.test_request_context():
            result = test_route()
            assert result.status_code == 302
            assert result.location == "/coming-soon"

    def test_require_flag_custom_expected_value(self, ld_client, flask_app, test_data, request_context):
        """Test @require_flag with custom expected_value."""
        # Set up flag in TestData with string variation
        test_data.update(test_data.flag("test-feature").value_for_all("beta"))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        @require_flag("test-feature", default="stable", expected_value="beta")
        def test_route():
            return "Beta feature!"
        
        result = test_route()
        assert result == "Beta feature!"

    def test_require_flag_custom_expected_value_no_match(self, ld_client, flask_app, test_data, request_context):
        """Test @require_flag with custom expected_value that doesn't match."""
        # Set up flag in TestData with string variation
        test_data.update(test_data.flag("test-feature").value_for_all("stable"))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        @require_flag("test-feature", default="stable", expected_value="beta")
        def test_route():
            return "Beta feature!"
        
        with pytest.raises(Exception):  # Flask's abort raises an exception
            test_route()

    def test_require_flag_without_context(self, ld_client, flask_app, test_data, request_context):
        """Test @require_flag when no LD context is set."""
        # Set up flag in TestData
        test_data.update(test_data.flag("test-feature").variation_for_all(True))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # No context set
        
        @require_flag("test-feature", default=False)
        def test_route():
            return "Feature enabled!"
        
        with pytest.raises(Exception):  # Should abort due to default=False
            test_route()


class TestWithContextDecorator:
    """Test @with_context decorator."""

    def test_with_context_callable(self, ld_client, flask_app, request_context):
        """Test @with_context with callable context function."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        def context_fn():
            return Context.builder("decorator-user").build()
        
        @with_context(context_fn)
        def test_route():
            return g.ld_context.key
        
        result = test_route()
        assert result == "decorator-user"

    def test_with_context_direct_context(self, ld_client, flask_app, request_context):
        """Test @with_context with direct Context object."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        context = Context.builder("direct-user").build()
        
        @with_context(context)
        def test_route():
            return g.ld_context.key
        
        result = test_route()
        assert result == "direct-user"

    def test_with_context_none_context(self, ld_client, flask_app, request_context):
        """Test @with_context with None context."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        @with_context(None)
        def test_route():
            return "No context set"
        
        result = test_route()
        assert result == "No context set"

    def test_with_context_existing_context(self, ld_client, flask_app, request_context):
        """Test @with_context when context already exists (should create multi-context)."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set existing context
        existing_context = Context.builder("existing-user").build()
        g.ld_context = existing_context
        
        def context_fn():
            return Context.builder("decorator-user").kind("role").build()
        
        @with_context(context_fn)
        def test_route():
            return g.ld_context.individual_context_count
        
        result = test_route()
        assert result == 2  # Should have 2 contexts


class TestTrackAfterDecorator:
    """Test @track_after decorator."""

    def test_track_after_basic(self, ld_client, flask_app, request_context):
        """Test @track_after decorator basic functionality."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        @track_after("user-action")
        def test_route():
            return "Action completed"
        
        result = test_route()
        assert result == "Action completed"
        
        extension._client.track.assert_called_once_with(
            "user-action", 
            context, 
            data=None, 
            metric_value=None
        )

    def test_track_after_with_data(self, ld_client, flask_app, request_context):
        """Test @track_after decorator with custom data."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        @track_after("user-action", data={"action": "profile-view"})
        def test_route():
            return "Action completed"
        
        test_route()
        
        extension._client.track.assert_called_once_with(
            "user-action", 
            context, 
            data={"action": "profile-view"}, 
            metric_value=None
        )

    def test_track_after_with_metric_value(self, ld_client, flask_app, request_context):
        """Test @track_after decorator with metric value."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        @track_after("user-action", metric_value=1.5)
        def test_route():
            return "Action completed"
        
        test_route()
        
        extension._client.track.assert_called_once_with(
            "user-action", 
            context, 
            data=None, 
            metric_value=1.5
        )

    def test_track_after_without_context(self, ld_client, flask_app, request_context):
        """Test @track_after decorator without LD context."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        @track_after("user-action")
        def test_route():
            return "Action completed"
        
        result = test_route()
        assert result == "Action completed"
        
        # Should not call client.track
        extension._client.track.assert_not_called()


class TestTrackBeforeDecorator:
    """Test @track_before decorator."""

    def test_track_before_basic(self, ld_client, flask_app, request_context):
        """Test @track_before decorator basic functionality."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        @track_before("api-call")
        def test_route():
            return "API response"
        
        result = test_route()
        assert result == "API response"
        
        extension._client.track.assert_called_once_with(
            "api-call", 
            context, 
            data=None, 
            metric_value=None
        )

    def test_track_before_with_data(self, ld_client, flask_app, request_context):
        """Test @track_before decorator with custom data."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        @track_before("api-call", data={"endpoint": "user-profile"})
        def test_route():
            return "API response"
        
        test_route()
        
        extension._client.track.assert_called_once_with(
            "api-call", 
            context, 
            data={"endpoint": "user-profile"}, 
            metric_value=None
        )

    def test_track_before_with_metric_value(self, ld_client, flask_app, request_context):
        """Test @track_before decorator with metric value."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        @track_before("api-call", metric_value=2.0)
        def test_route():
            return "API response"
        
        test_route()
        
        extension._client.track.assert_called_once_with(
            "api-call", 
            context, 
            data=None, 
            metric_value=2.0
        )

    def test_track_before_without_context(self, ld_client, flask_app, request_context):
        """Test @track_before decorator without LD context."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        @track_before("api-call")
        def test_route():
            return "API response"
        
        result = test_route()
        assert result == "API response"
        
        # Should not call client.track
        extension._client.track.assert_not_called()


class TestDecoratorStacking:
    """Test decorator stacking scenarios."""

    def test_decorator_stacking(self, ld_client, flask_app, test_data, request_context):
        """Test stacking multiple decorators."""
        # Set up flag in TestData
        test_data.update(test_data.flag("test-feature").variation_for_all(True))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Mock client.track
        extension._client.track = MagicMock()
        
        def context_fn():
            return Context.builder("decorator-user").kind("role").build()
        
        @require_flag("test-feature", default=False)
        @with_context(context_fn)
        @track_before("before-action")
        @track_after("after-action")
        def test_route():
            return "Stacked decorators!"
        
        result = test_route()
        assert result == "Stacked decorators!"
        
        # Should have called track twice (before and after)
        assert extension._client.track.call_count == 2
