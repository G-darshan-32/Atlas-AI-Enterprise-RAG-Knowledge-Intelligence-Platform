from pydantic import BaseModel, field_validator
from typing import Optional, List, Any


class SearchFilters(BaseModel):
    file_type: Optional[str] = None
    source_type: Optional[str] = None
    document_id: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    filters: Optional[SearchFilters] = None
    limit: int = 10

    @field_validator("limit")
    @classmethod
    def clamp_limit(cls, v: int) -> int:
        return max(1, min(v, 50))


class SearchResultItem(BaseModel):
    chunk_id: str
    document_id: Optional[str]
    title: str
    file_type: str
    content: str
    score: float
    page_number: Optional[int]
    tags: Optional[List[str]]
    chunk_index: int


class SearchResponse(BaseModel):
    query: str
    total: int
    results: List[SearchResultItem]
