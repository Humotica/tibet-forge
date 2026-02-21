"""
TIBET audit decorator.

@tibet_audit automatically creates provenance tokens.
"""

import functools
from typing import Optional, Callable, Any


def tibet_audit(
    action: Optional[str] = None,
    erachter: str = "",
    capture_args: bool = True,
    capture_result: bool = False
):
    """
    Decorator to add TIBET provenance to a function.

    Example:
        @tibet_audit(action="user_login", erachter="Authentication")
        def login(username, password):
            ...

    Args:
        action: Action name (defaults to function name)
        erachter: Intent/reason
        capture_args: Include args in ERIN
        capture_result: Include return value in ERIN
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get or create TIBET provider
            tibet = _get_tibet_provider()

            # Build ERIN
            erin = {}
            if capture_args:
                erin["args_count"] = len(args)
                erin["kwargs_keys"] = list(kwargs.keys())

            # Create pre-call token
            if tibet:
                token = tibet.create(
                    action=action or func.__name__,
                    erin=erin,
                    erachter=erachter or f"Calling {func.__name__}"
                )

            # Call function
            result = func(*args, **kwargs)

            # Create post-call token
            if tibet and capture_result:
                tibet.create(
                    action=f"{action or func.__name__}_result",
                    erin={"result_type": type(result).__name__},
                    erachter=f"Completed {func.__name__}",
                    parent_id=token.token_id
                )

            return result

        return wrapper
    return decorator


# Global TIBET provider (can be set by user)
_tibet_provider = None


def set_tibet_provider(provider):
    """Set the global TIBET provider."""
    global _tibet_provider
    _tibet_provider = provider


def _get_tibet_provider():
    """Get the global TIBET provider."""
    return _tibet_provider
