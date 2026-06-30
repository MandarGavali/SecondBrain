class SecondBrainError(Exception):
    """Base exception for all custom SecondBrain errors."""
    pass

class GeminiError(SecondBrainError):
    """Raised when communication with Gemini fails."""
    pass

class RetrieverError(SecondBrainError):
    """Raised when document retrieval or Qdrant fails."""
    pass

class MemoryError(SecondBrainError):
    """Raised when memory operations (MongoDB/Short-Term) fail."""
    pass

class MCPError(SecondBrainError):
    """Raised when an MCP tool execution fails."""
    pass

class ValidationError(SecondBrainError):
    """Raised when input validation fails."""
    pass
