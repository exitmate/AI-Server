from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)

class SearchResponse(BaseModel):
    question: str
    answer: str
