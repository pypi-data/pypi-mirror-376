"""Query tool implementation for MCP server."""

from typing import Optional
import logging
from ..services.seekr_client import ISeekrClient
from ..seekr_types.seekr import (
    Engine,
    QueryType,
    TimeRange,
    SafeQueryLevel,
    SeekrQueryParams,
    SeekrPrismParams,
    SeekrQueryResponse,
    SeekrPrismResponse,
)

logger = logging.getLogger(__name__)


class SeekrQueryTools:
    """Query tool implementation for MCP server."""

    def __init__(self, client: ISeekrClient):
        """Initialize query tool with Seekr client.

        Args:
            client: Seekr API client instance
        """
        self.seekr_client = client

    async def query(
        self,
        query: str,
        engine: Optional[str] = None,
        language: Optional[str] = None,
        region: Optional[str] = None,
        safe_search: Optional[int] = None,
        time_range: Optional[str] = None,
        page: Optional[int] = None,
        search_type: Optional[str] = None,
        num: Optional[int] = None,
    ) -> SeekrQueryResponse:
        """Execute a web query.

        Args:
            query: Query string
            engine: Query engine to use ("google", "wikipedia")
            language: Language code (ISO 639-1)
            region: Region code (ISO 3166-1 alpha-2)
            safe_search: Safe query level (0=off, 1=medium, 2=high)
            time_range: Time filter ("day", "week", "month", "year")
            page: Page number (1-based)
            search_type: Type of query ("web", "images", "videos", "news")
            num: Number of results to return

        Returns:
            Query results from Seekr API

        Raises:
            ValueError: If query fails
        """
        try:
            # Build query parameters
            params: SeekrQueryParams = {
                "query": query,
            }

            # Add optional parameters
            if engine:
                params["engine"] = Engine(engine)
            if language:
                params["language"] = language
            if region:
                params["region"] = region
            if safe_search is not None:
                params["safe_search"] = SafeQueryLevel(safe_search)
            if time_range:
                params["time_range"] = TimeRange(time_range)
            if page:
                params["page"] = page
            if search_type:
                params["search_type"] = QueryType(search_type)
            if num:
                params["num"] = num

            logger.info(
                f"Querying with query: '{query}' using engine: {engine or 'google'}"
            )
            result = await self.seekr_client.search(params)
            logger.info(
                f"Query completed, returned {len(result.get('results', []))} results"
            )

            return result

        except Exception as e:
            logger.error(f"Query failed for query '{query}': {str(e)}")
            raise ValueError(f'QueryTool: failed to query for "{query}". {str(e)}')

    async def prism(
        self,
        url: str,
        language: Optional[str] = None,
    ) -> SeekrPrismResponse:
        """Execute a web scrape operation.

        Args:
            url: URL to scrape
            language: Language for content extraction

        Returns:
            Scraped content from Seekr API

        Raises:
            ValueError: If scraping fails
        """
        try:
            # Build prism parameters
            params: SeekrPrismParams = {
                "url": url,
                "engine": Engine.PRISM,
            }

            if language:
                params["language"] = language

            logger.info(f"Prisming content from URL: {url}")
            result = await self.seekr_client.fetch(params)
            logger.info(f"Prism completed for URL: {url}")

            return result

        except Exception as e:
            logger.error(f"Prism failed for URL '{url}': {str(e)}")
            raise ValueError(f'QueryTool: failed to prism from "{url}". {str(e)}')

    async def advanced_query(
        self,
        query: str,
        site: Optional[str] = None,
        filetype: Optional[str] = None,
        inurl: Optional[str] = None,
        intitle: Optional[str] = None,
        exact: Optional[str] = None,
        exclude: Optional[str] = None,
        or_terms: Optional[str] = None,
        **kwargs,
    ) -> SeekrQueryResponse:
        """Execute an advanced query with operators.

        This method constructs an advanced query by appending
        Google query operators to the base query.

        Args:
            query: Base query
            site: Limit results to specific domain
            filetype: Limit to specific file types
            inurl: Query for pages with word in URL
            intitle: Query for pages with word in title
            exact: Exact phrase match
            exclude: Terms to exclude (comma-separated)
            or_terms: Alternative terms (comma-separated)
            **kwargs: Additional query parameters

        Returns:
            Query results from Seekr API
        """
        # Build advanced query with operators
        advanced_query = query.strip()

        if site:
            advanced_query += f" site:{site}"
        if filetype:
            advanced_query += f" filetype:{filetype}"
        if inurl:
            advanced_query += f" inurl:{inurl}"
        if intitle:
            advanced_query += f" intitle:{intitle}"
        if exact:
            advanced_query += f' "{exact}"'
        if exclude:
            for term in exclude.split(","):
                advanced_query += f" -{term.strip()}"
        if or_terms:
            terms = [term.strip() for term in or_terms.split(",")]
            advanced_query += f" ({' OR '.join(terms)})"

        logger.info(f"Advanced query: {advanced_query}")

        # Execute query with the constructed query
        return await self.query(query=advanced_query, **kwargs)
