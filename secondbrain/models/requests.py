from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    # Conversation id. Ints are still accepted for backward compatibility.
    thread_id: int | str = "default"
