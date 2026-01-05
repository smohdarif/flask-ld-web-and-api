"""
Tests for LaunchDarkly context management functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, g, has_request_context, request
from ldclient import Context

from launchdarkly.contexts import (
    create_request_context,
    replace_context,
    add_context,
    remove_context,
    get_context,
    current_context,
    _context_kind_dict,
    _context_iter
)


class TestCreateRequestContext:
    """Test create_request_context function."""

    def test_create_request_context_with_key(self, flask_app):
        """Test creating request context with custom key."""
        @flask_app.route('/test')
        def test_route():
            pass
            
        with flask_app.test_request_context('/test', method='GET'):
            context = create_request_context(key="custom-key")
            
            assert context.key == "custom-key"
            assert context.kind == "x_ld_request"
            assert context.anonymous is True
            assert context.get("route") == "/test"
            assert context.get("method") == "GET"
            assert context.get("baseUrl") == "http://localhost/test"
            assert context.get("hostname") == "localhost"

    def test_create_request_context_without_key(self, flask_app):
        """Test creating request context without key (generates UUID)."""
        @flask_app.route('/test')
        def test_route():
            pass
            
        with flask_app.test_request_context('/test', method='POST'):
            context = create_request_context()
            
            assert context.key is not None
            assert len(context.key) == 36  # UUID length
            assert context.kind == "x_ld_request"
            assert context.get("method") == "POST"

    def test_create_request_context_with_additional_attributes(self, flask_app):
        """Test creating request context with additional attributes."""
        @flask_app.route('/test')
        def test_route():
            pass
            
        with flask_app.test_request_context('/test'):
            context = create_request_context(
                key="test-key",
                custom_attr="custom_value",
                number_attr=42
            )
            
            assert context.get("custom_attr") == "custom_value"
            assert context.get("number_attr") == 42

    def test_create_request_context_without_url_rule(self, flask_app):
        """Test creating request context when url_rule is None."""
        with flask_app.test_request_context('/test'):
            # Mock url_rule to be None
            request.url_rule = None
            
            context = create_request_context()
            
            assert context.get("route") is None


class TestReplaceContext:
    """Test replace_context function."""

    def test_replace_context(self, flask_app, request_context):
        """Test replacing context in Flask g."""
        context = Context.builder("test-user").build()
        
        replace_context(context)
        
        assert g.ld_context == context


class TestAddContext:
    """Test add_context function."""

    def test_add_context_no_existing(self, flask_app, request_context):
        """Test adding context when no existing context."""
        context = Context.builder("test-user").build()
        
        add_context(context)
        
        assert g.ld_context == context

    def test_add_context_with_existing_single(self, flask_app, request_context):
        """Test adding context when single context already exists."""
        existing_context = Context.builder("existing-user").build()
        g.ld_context = existing_context
        
        new_context = Context.builder("new-user").kind("role").build()
        
        add_context(new_context)
        
        # Should create multi-context
        assert g.ld_context.individual_context_count == 2
        
        # Check that both contexts are present (order may vary)
        keys = [g.ld_context.get_individual_context(i).key for i in range(2)]
        assert "existing-user" in keys
        assert "new-user" in keys

    def test_add_context_with_existing_multi(self, flask_app, request_context):
        """Test adding context when multi-context already exists."""
        # Create multi-context
        user_context = Context.builder("user").build()
        role_context = Context.builder("admin").kind("role").build()
        existing_multi = Context.multi_builder().add(user_context).add(role_context).build()
        g.ld_context = existing_multi
        
        new_context = Context.builder("session").kind("session").build()
        
        add_context(new_context)
        
        # Should have 3 contexts
        assert g.ld_context.individual_context_count == 3


class TestRemoveContext:
    """Test remove_context function."""

    def test_remove_context_no_existing(self, flask_app, request_context):
        """Test removing context when no context exists."""
        # Should not raise exception
        remove_context("user")

    def test_remove_context_single_context(self, flask_app, request_context):
        """Test removing context from single context."""
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        remove_context("user")
        
        # Should remove the context
        assert g.ld_context is None

    def test_remove_context_multi_context(self, flask_app, request_context):
        """Test removing context from multi-context."""
        # Create multi-context
        user_context = Context.builder("user").build()
        role_context = Context.builder("admin").kind("role").build()
        session_context = Context.builder("session").kind("session").build()
        multi_context = Context.multi_builder().add(user_context).add(role_context).add(session_context).build()
        g.ld_context = multi_context
        
        remove_context("role")
        
        # Should have 2 contexts left
        assert g.ld_context.individual_context_count == 2
        
        # Check that both remaining contexts are present (order may vary)
        kinds = [g.ld_context.get_individual_context(i).kind for i in range(2)]
        assert "user" in kinds
        assert "session" in kinds


class TestGetContext:
    """Test get_context function."""

    def test_get_context_with_context(self, flask_app, request_context):
        """Test getting context when context exists."""
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        result = get_context()
        assert result == context

    def test_get_context_no_context(self, flask_app, request_context):
        """Test getting context when no context exists."""
        result = get_context()
        assert result is None

    def test_get_context_outside_request(self, flask_app):
        """Test getting context outside request context."""
        result = get_context()
        assert result is None


class TestCurrentContextProxy:
    """Test current_context LocalProxy."""

    def test_current_context_proxy(self, flask_app, request_context):
        """Test current_context LocalProxy."""
        context = Context.builder("test-user").build()
        g.ld_context = context
        
        assert current_context == context

    def test_current_context_proxy_no_context(self, flask_app, request_context):
        """Test current_context LocalProxy when no context."""
        # Ensure no context is set
        if hasattr(g, 'ld_context'):
            delattr(g, 'ld_context')
        
        # The LocalProxy should return None when no context is set
        result = current_context
        assert result is None or str(result) == 'None'


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_context_kind_dict_single(self):
        """Test _context_kind_dict with single context."""
        context = Context.builder("test-user").build()
        result = _context_kind_dict(context)
        
        assert len(result) == 1
        assert "user" in result
        assert result["user"].key == "test-user"

    def test_context_kind_dict_multi(self):
        """Test _context_kind_dict with multi-context."""
        user_context = Context.builder("user").build()
        role_context = Context.builder("admin").kind("role").build()
        multi_context = Context.multi_builder().add(user_context).add(role_context).build()
        
        result = _context_kind_dict(multi_context)
        
        assert len(result) == 2
        assert "user" in result
        assert "role" in result
        assert result["user"].key == "user"
        assert result["role"].key == "admin"

    def test_context_iter_single(self):
        """Test _context_iter with single context."""
        context = Context.builder("test-user").build()
        contexts = list(_context_iter(context))
        
        assert len(contexts) == 1
        assert contexts[0].key == "test-user"

    def test_context_iter_multi(self):
        """Test _context_iter with multi-context."""
        user_context = Context.builder("user").build()
        role_context = Context.builder("admin").kind("role").build()
        multi_context = Context.multi_builder().add(user_context).add(role_context).build()
        
        contexts = list(_context_iter(multi_context))
        
        assert len(contexts) == 2
        
        # Check that both contexts are present (order may vary)
        keys = [c.key for c in contexts]
        assert "user" in keys
        assert "admin" in keys
