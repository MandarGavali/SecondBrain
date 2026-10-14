from typing import Optional
from pydantic import BaseModel


class ChatResponse(BaseModel):
    answer: str
    confidence: str                          # High | Medium | Low | N/A | Unverified
    confidence_score: Optional[float] = None
    route: Optional[str] = None              # no_search | simple | complex
    grounded: Optional[bool] = None
    abstained: bool = False
    needs_review: bool = False
    sources: list[dict] = []
    metrics: dict = {}
    reflection: Optional[dict] = None
