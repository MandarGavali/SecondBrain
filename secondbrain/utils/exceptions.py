class SecondBrainException(Exception):
    """Base exception for all custom project exceptions."""
    pass

class RetrievalError(SecondBrainException):
    """Raised when document retrieval fails (e.g. Qdrant or Embedding issues)."""
    pass

class GenerationError(SecondBrainException):
    """Raised when the LLM fails to generate an answer."""
    pass

class RoutingError(SecondBrainException):
    """Raised when the query router fails to determine a valid route."""
    pass

class ValidationError(SecondBrainException):
    """Raised when the graph state is missing required fields."""
    pass

class GraphExecutionError(SecondBrainException):
    """Raised when an unexpected error occurs during graph execution."""
    pass
