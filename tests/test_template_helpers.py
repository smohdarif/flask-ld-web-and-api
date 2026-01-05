"""
Tests for LaunchDarkly Jinja2 template helpers.
"""
import pytest
from flask import Flask, render_template_string, g
from ldclient import Context

from launchdarkly import LaunchDarkly


class TestTemplateHelpers:
    """Test Jinja2 template helper functions."""

    def test_ld_variation_boolean_flag(self, ld_client, flask_app, test_data, request_context):
        """Test ld_variation helper with boolean flag."""
        # Set up flag in TestData
        test_data.update(test_data.flag("show-banner").variation_for_all(True))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Test template rendering
        template = "{% if ld_variation('show-banner', False) %}Banner shown{% else %}Banner hidden{% endif %}"
        result = render_template_string(template)
        assert "Banner shown" in result

    def test_ld_variation_string_flag(self, ld_client, flask_app, test_data, request_context):
        """Test ld_variation helper with string flag."""
        # Set up flag in TestData - need to use value_for_all for string values
        test_data.update(test_data.flag("theme").value_for_all("dark"))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Test template rendering
        template = "{{ ld_variation('theme', 'light') }}"
        result = render_template_string(template)
        assert result == "dark"

    def test_ld_variation_number_flag(self, ld_client, flask_app, test_data, request_context):
        """Test ld_variation helper with number flag."""
        # Set up flag in TestData - need to use value_for_all for number values
        test_data.update(test_data.flag("max-items").value_for_all(25))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Test template rendering
        template = "{{ ld_variation('max-items', 10) }}"
        result = render_template_string(template)
        assert result == "25"

    def test_ld_variation_default_value(self, ld_client, flask_app, test_data, request_context):
        """Test ld_variation helper returns default when flag not found."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        # Test template rendering with non-existent flag
        template = "{{ ld_variation('non-existent-flag', 'default-value') }}"
        result = render_template_string(template)
        assert result == "default-value"

    def test_ld_variation_without_context(self, ld_client, flask_app, test_data):
        """Test ld_variation helper without LaunchDarkly context."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # No context set
        
        # Test template rendering within app context
        with flask_app.app_context():
            template = "{{ ld_variation('test-flag', 'fallback') }}"
            result = render_template_string(template)
            assert result == "fallback"

    def test_ld_context_helper(self, ld_client, flask_app, test_data, request_context):
        """Test ld_context helper returns current context."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("test-user").set("email", "user@example.com").build()
        g.ld_context = context
        
        # Test template rendering
        template = "{{ ld_context().key }}"
        result = render_template_string(template)
        assert result == "test-user"

    def test_ld_context_helper_no_context(self, ld_client, flask_app, test_data):
        """Test ld_context helper when no context is set."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # No context set
        
        # Test template rendering within app context
        with flask_app.app_context():
            template = "{{ ld_context() }}"
            result = render_template_string(template)
            assert result == "None"

    def test_template_helpers_registered(self, ld_client, flask_app):
        """Test that template helpers are properly registered."""
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Check that helpers are registered in Jinja environment
        assert 'ld_variation' in flask_app.jinja_env.globals
        assert 'ld_context' in flask_app.jinja_env.globals
        
        # Check that they are callable
        assert callable(flask_app.jinja_env.globals['ld_variation'])
        assert callable(flask_app.jinja_env.globals['ld_context'])

    def test_complex_template_scenario(self, ld_client, flask_app, test_data, request_context):
        """Test complex template scenario with multiple flags."""
        # Set up multiple flags - need to call update separately for each
        test_data.update(test_data.flag("show-banner").variation_for_all(True))
        test_data.update(test_data.flag("theme").value_for_all("dark"))
        test_data.update(test_data.flag("max-items").value_for_all(50))
        
        extension = LaunchDarkly(ld_client, flask_app)
        
        # Set up context
        context = Context.builder("premium-user").build()
        g.ld_context = context
        
        # Complex template
        template = """
        {% if ld_variation('show-banner', False) %}
            <div class="banner theme-{{ ld_variation('theme', 'light') }}">
                Premium features available!
            </div>
        {% endif %}
        <div class="content">
            Showing {{ ld_variation('max-items', 10) }} items
        </div>
        """
        
        result = render_template_string(template)
        
        # Verify all parts are rendered correctly
        assert "banner theme-dark" in result
        assert "Premium features available!" in result
        assert "Showing 50 items" in result
