"""Seekr API client implementation."""

import asyncio
import os
from typing import Protocol, Optional, Dict, Any, cast
import httpx
from ..seekr_types.seekr import (
    Engine,
    SeekrQueryParams,
    SeekrPrismParams,
    SeekrQueryResponse,
    SeekrPrismResponse,
)


class ISeekrClient(Protocol):
    """Interface for Seekr API client to allow mocking in tests."""

    async def search(self, params: SeekrQueryParams) -> SeekrQueryResponse:
        """Perform a query using Seekr API."""
        ...

    async def fetch(self, params: SeekrPrismParams) -> SeekrPrismResponse:
        """Prism and scrape a URL using Seekr API."""
        ...


class SeekrClient:
    """Implementation of Seekr API client."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        """Initialize Seekr API client.

        Args:
            base_url: Base URL for Seekr API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = (
            base_url or os.getenv("SEEKR_BASE_URL", "https://engine.seekr.sh")
        )
        if self.base_url:
            self.base_url = self.base_url.rstrip("/")
        self.timeout = timeout or float(os.getenv("SEEKR_TIMEOUT", "30.0"))
        self.max_retries = max_retries or int(os.getenv("SEEKR_MAX_RETRIES", "3"))
        self.api_key = os.getenv("SEEKR_API_KEY")

    async def _make_request(self, method: str, endpoint: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Seekr API with retries.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: JSON data to send in request body

        Returns:
            Response data as dictionary

        Raises:
            httpx.HTTPError: If request fails after all retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.request(
                        method=method, url=url, json=json_data, headers=headers
                    )
                    response.raise_for_status()
                    return response.json()

                except (httpx.HTTPError, httpx.TimeoutException) as e:
                    if attempt == self.max_retries - 1:
                        raise httpx.HTTPError(
                            f"Seekr API request failed after {self.max_retries} attempts: {str(e)}"
                        )

                    # Exponential backoff
                    await asyncio.sleep(2**attempt)
                    continue

        # Should never reach here but satisfies type checker
        raise httpx.HTTPError("Unexpected error in request handling")

    async def search(self, params: SeekrQueryParams) -> SeekrQueryResponse:
        """Perform a query using Seekr API.

        Args:
            params: Query parameters

        Returns:
            Query response from Seekr API

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If required parameters are missing
        """
        if not params.get("query"):
            raise ValueError("Query parameter is required for query operations")

        # Set defaults
        request_data = {
            "query": params["query"],
            "engine": params.get("engine", Engine.GOOGLE.value),
            "language": params.get("language", "en"),
            "region": params.get("region", "US"),
            "safe_search": params.get("safe_search", 0),
            "page": params.get("page", 1),
            "search_type": params.get("search_type", "web"),
        }

        # Add optional parameters
        if params.get("time_range"):
            request_data["time_range"] = params["time_range"]
        if params.get("num"):
            request_data["num"] = params["num"]

        try:
            response_data = await self._make_request(
                "POST", "/api/search", request_data
            )

            # Check if response contains error
            if "error" in response_data:
                error_msg = response_data["error"]
                raise httpx.HTTPError(f"Seekr API error: {error_msg}")

            return cast(SeekrQueryResponse, response_data)

        except Exception as e:
            raise httpx.HTTPError(f"Query failed: {str(e)}")

    async def fetch(self, params: SeekrPrismParams) -> SeekrPrismResponse:
        """Prism and scrape a URL using Seekr API.

        Args:
            params: Prism parameters

        Returns:
            Prism response from Seekr API

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If required parameters are missing
        """
        if not params.get("url"):
            raise ValueError("URL parameter is required for prism operations")

        # Set up request data for prism engine
        request_data = {
            "url": params["url"],
            "engine": Engine.PRISM.value,
        }

        try:
            response_data = await self._make_request(
                "POST", "/api/search", request_data
            )

            # Check if response contains error
            if "error" in response_data:
                error_msg = response_data["error"]
                raise httpx.HTTPError(f"Seekr API error: {error_msg}")

            # Return raw API response
            return cast(SeekrPrismResponse, response_data)

        except Exception as e:
            raise httpx.HTTPError(f"Prism failed: {str(e)}")


# Create default client instance
default_client = SeekrClient()
