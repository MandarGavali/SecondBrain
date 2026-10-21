"""
Backward-compatible exception names.

These used to be a second, separate hierarchy (SecondBrainException), so the
API's SecondBrainError handler in main.py never caught them and retrieval
errors raised as core.RetrieverError slipped past `except RetrievalError`.
They now all derive from secondbrain.core.exceptions.SecondBrainError.
"""

from secondbrain.core.exceptions import (
    RetrieverError,
    SecondBrainError,
    ValidationError,
)

SecondBrainException = SecondBrainError

# Same class as core.RetrieverError so either name catches retrieval failures.
RetrievalError = RetrieverError


class GenerationError(SecondBrainError):
    """Raised when the LLM fails to generate an answer."""


class RoutingError(SecondBrainError):
    """Raised when the query router fails to determine a valid route."""


class GraphExecutionError(SecondBrainError):
    """Raised when an unexpected error occurs during graph execution."""


__all__ = [
    "SecondBrainException",
    "RetrievalError",
    "GenerationError",
    "RoutingError",
    "ValidationError",
    "GraphExecutionError",
]
