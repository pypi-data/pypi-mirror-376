"""Type definitions for Seekr API requests and responses."""

from typing import List, Optional, TypedDict, Literal, Any, Dict
from enum import Enum


class Engine(str, Enum):
    """Supported query engines."""

    GOOGLE = "google"
    PRISM = "prism"


class QueryType(str, Enum):
    """Supported query types for Google."""

    WEB = "web"
    IMAGES = "images"
    VIDEOS = "videos"
    NEWS = "news"


class TimeRange(str, Enum):
    """Supported time ranges for filtering results."""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class SafeQueryLevel(int, Enum):
    """Safe query filtering levels."""

    OFF = 0
    MEDIUM = 1
    HIGH = 2


class SeekrQueryParams(TypedDict, total=False):
    """Query parameters for Seekr API."""

    query: str  # Required for query operations
    engine: Engine
    language: Optional[str]  # Language code (ISO 639-1)
    region: Optional[str]  # Region code (ISO 3166-1 alpha-2)
    safe_search: Optional[SafeQueryLevel]  # Safe query level
    time_range: Optional[TimeRange]  # Time filter
    page: Optional[int]  # Page number (1-based)
    search_type: Optional[QueryType]  # Type of query
    num: Optional[int]  # Number of results (max 100 for Google, 50 for Wikipedia)


class SeekrPrismParams(TypedDict, total=False):
    """Prism parameters for Seekr API."""

    url: str  # Required for prism operations
    engine: Literal[Engine.PRISM]
    language: Optional[str]  # Language for content extraction


class QueryResult(TypedDict, total=False):
    """Individual query result."""

    title: str
    url: str
    description: str
    position: int
    # Wikipedia-specific metadata
    metadata: Optional[Dict[str, Any]]  # pageid, size, wordcount, timestamp


class SeekrQueryResponse(TypedDict, total=False):
    """Response from Seekr query API."""

    results: List[QueryResult]
    suggestions: Optional[List[str]]
    search_type: Optional[str]
    engine: str


class SeekrPrismResponse(TypedDict, total=False):
    """Response from Seekr prism API."""

    content: str
    url: str
    timestamp: Optional[str]
    source: Optional[str]
    metadata: Optional[Dict[str, Any]]


class SeekrError(TypedDict):
    """Error response from Seekr API."""

    error: str


# Union types for responses
SeekrResponse = SeekrQueryResponse | SeekrPrismResponse | SeekrError
