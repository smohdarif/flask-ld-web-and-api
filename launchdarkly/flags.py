"""
LaunchDarkly flag evaluation helpers.
Provides convenient wrapper functions for flag evaluation.
"""
from flask import g
from launchdarkly import get_client


def get_flag(flag_key, default=False):
    """
    Wrapper function for ld.variation that uses g.ld_context from request context.
    
    Args:
        flag_key: The LaunchDarkly flag key
        default: Default value if flag evaluation fails
    
    Returns:
        The flag variation value
    """
    ld_client = get_client()
    return ld_client.variation(flag_key, g.ld_context, default=default)
