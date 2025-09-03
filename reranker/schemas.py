from pydantic import BaseModel
from typing import List

class RerankRequest(BaseModel):
    query: str
    passages: List[str]
    top_k: int = 5

class RerankResult(BaseModel):
    text: str
    score: float
    index: int

class RerankResponse(BaseModel):
    results: List[RerankResult]