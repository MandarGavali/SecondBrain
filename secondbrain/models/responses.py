#defines what the API returns 

from pydantic import BaseModel

class ChatResponse(BaseModel):
    answer : str
    confidence : str