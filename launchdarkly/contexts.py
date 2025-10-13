from typing import Optional, Dict, Any
from uuid import uuid4
from contextlib import contextmanager
from flask import g, has_request_context, request
from ldclient import Context

from werkzeug.local import LocalProxy

current_context = LocalProxy(lambda: get_context())

__all__ = [
    'create_request_context',
    'replace_context', 
    'add_context',
    'remove_context',
    'get_context',
    'use_context',
    'current_context'
]


def create_request_context(key: Optional[str] = None, **additional_attributes) -> Context:
    """
    Build a LaunchDarkly context from Flask request object
    
    Args:
        key: The key of the context. Should be a request identifier. Default is a random UUID.
        additional_attributes: Additional attributes to set on the context
    
    Returns:
        LaunchDarkly Context with kind 'x_ld_request'
    """
    if key is None:
        key = str(uuid4())
    
    # Get the matched route pattern if available
    route_path = None
    if request.url_rule:
        route_path = request.url_rule.rule
    
    builder = Context.builder(key).kind("x_ld_request").anonymous(True)\
        .set("route", route_path)\
        .set("method", request.method)\
        .set("baseUrl", request.base_url)\
        .set("ipAddress", request.remote_addr)\
        .set("hostname", request.host)
    
    for attr_key, value in additional_attributes.items():
        builder.set(attr_key, value)
    
    return builder.build()


def replace_context(context: Context):
    """
    Set the LaunchDarkly context for the current request.
    
    Args:
        context: LaunchDarkly Context to set
    """
    g.ld_context = context


def add_context(context: Context):
    """
    Add a context to the current request, creating a multi-context if needed.
    
    Args:
        context: LaunchDarkly Context to add
    """
    existing = getattr(g, 'ld_context', None)
    if existing is None:
        g.ld_context = context
        return
    
    # Build multi-context
    new_contexts = _context_kind_dict(existing)
    new_contexts.update(_context_kind_dict(context))
    
    # Create multi-context using the builder
    builder = Context.multi_builder()
    for individual_context in new_contexts.values():
        builder.add(individual_context)
    g.ld_context = builder.build()

def remove_context(kind: str):
    """
    Remove a context from the current request.
    
    Args:
        kind: The kind of the context to remove
    """
    existing = getattr(g, 'ld_context', None)
    if existing is None:
        return
    
    remaining_contexts = [c for c in _context_iter(existing) if c.kind != kind]
    
    if not remaining_contexts:
        g.ld_context = None
    elif len(remaining_contexts) == 1:
        g.ld_context = remaining_contexts[0]
    else:
        builder = Context.multi_builder()
        for context in remaining_contexts:
            builder.add(context)
        g.ld_context = builder.build()


def get_context() -> Optional[Context]:
    """
    Get the LaunchDarkly context from the current request.
    
    Returns:
        LaunchDarkly Context or None
    """
    if has_request_context() and hasattr(g, 'ld_context'):
        return g.ld_context
    return None


def _context_kind_dict(context: Context):
    """
    Convert a LaunchDarkly context to a dictionary of kind to context.
    
    Args:
        context: LaunchDarkly Context
    
    Returns:
        Dictionary mapping context kind to individual context
    """
    context_dict = {}
    for individual in _context_iter(context):
        context_dict[individual.kind] = individual
    return context_dict

def _context_iter(context: Context):
    """
    Iterate over the individual contexts in a LaunchDarkly context.
    
    Args:
        context: LaunchDarkly Context
    """
    for i in range(context.individual_context_count):
        yield context.get_individual_context(i)


@contextmanager
def use_context(context: Context):
    """
    Temporarily use a specific LaunchDarkly context, then restore the original.
    
    Args:
        context: LaunchDarkly Context to temporarily use
    
    Example:
        with use_context(create_user_context("test-user")):
            # Flag evaluations will use test-user context
            value = variation("my-flag")
        # Original context is restored
    """
    old = get_context()
    replace_context(context)
    try:
        yield
    finally:
        if old is not None:
            replace_context(old)
        else:
            g.ld_context = None