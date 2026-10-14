from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    thread_id: int
    user_id: Optional[str] = None     # defaults to str(thread_id) to preserve current behaviour
    session_end: bool = False         # True -> trigger AAM memory reflection after this turn
