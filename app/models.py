from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model matching Google Custom Search API"""
    q: str = Field(..., description="Search query")
    cx: Optional[str] = Field(None, description="Custom search engine ID (for compatibility)")
    num: Optional[int] = Field(10, ge=1, le=10, description="Number of results to return")
    start: Optional[int] = Field(1, ge=1, le=91, description="Index of first result")
    lr: Optional[str] = Field(None, description="Language restriction")
    safe: Optional[str] = Field("off", description="Safe search level")
    dateRestrict: Optional[str] = Field(None, description="Date restriction")


class SearchImage(BaseModel):
    """Image associated with search result"""
    contextLink: Optional[str] = None
    height: Optional[int] = None
    width: Optional[int] = None
    byteSize: Optional[int] = None
    thumbnailLink: Optional[str] = None
    thumbnailHeight: Optional[int] = None
    thumbnailWidth: Optional[int] = None


class PageMap(BaseModel):
    """Page metadata"""
    pass


class SearchItem(BaseModel):
    """Individual search result matching Google's format"""
    kind: str = "customsearch#result"
    title: str
    htmlTitle: str
    link: str
    displayLink: str
    snippet: str
    htmlSnippet: str
    cacheId: Optional[str] = None
    formattedUrl: str
    htmlFormattedUrl: str
    pagemap: Optional[Dict[str, Any]] = None
    mime: Optional[str] = None
    fileFormat: Optional[str] = None
    image: Optional[SearchImage] = None


class SearchInformation(BaseModel):
    """Search metadata"""
    searchTime: float
    formattedSearchTime: str
    totalResults: str
    formattedTotalResults: str


class Spelling(BaseModel):
    """Spelling correction"""
    correctedQuery: str
    htmlCorrectedQuery: str


class Query(BaseModel):
    """Query information"""
    title: str
    totalResults: str
    searchTerms: str
    count: int
    startIndex: int
    inputEncoding: str = "utf8"
    outputEncoding: str = "utf8"
    safe: str = "off"
    cx: Optional[str] = None


class Queries(BaseModel):
    """Previous and next page queries"""
    request: Optional[List[Query]] = None
    nextPage: Optional[List[Query]] = None
    previousPage: Optional[List[Query]] = None


class SearchResponse(BaseModel):
    """Response model matching Google Custom Search API"""
    kind: str = "customsearch#search"
    url: Dict[str, str]
    queries: Queries
    context: Optional[Dict[str, Any]] = None
    searchInformation: SearchInformation
    spelling: Optional[Spelling] = None
    items: Optional[List[SearchItem]] = []
