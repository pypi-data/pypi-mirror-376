#!/usr/bin/env python3
"""MCP server implementation that provides web query capabilities via Seekr API."""

import asyncio
import json
import logging
import os
import re
import sys
import time
from typing import Annotated, Dict, List
from urllib.parse import urlparse
from collections import defaultdict

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed

from fastmcp import FastMCP
from pydantic import Field

from .services.seekr_client import SeekrClient
from .tools.query_tool import SeekrQueryTools

# Set up logging with environment configuration
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Input validation functions
def validate_url(url: str) -> bool:
    """Validate URL format and security."""
    if not url or not isinstance(url, str) or len(url) > 2048:
        return False

    # Basic URL format validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP address
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if not url_pattern.match(url):
        return False

    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return False
        # Security checks
        if ".." in url or "<" in url or ">" in url or "javascript:" in url.lower():
            return False
        return True
    except Exception:
        return False


def validate_query_string(query: str) -> bool:
    """Validate query string."""
    if not query or not isinstance(query, str):
        return False

    query = query.strip()
    if len(query) == 0 or len(query) > 500:
        return False

    # Security check
    if "<" in query or ">" in query or "javascript:" in query.lower():
        return False

    return True


def validate_num_results(num: int) -> bool:
    """Validate number of results parameter."""
    return isinstance(num, int) and 1 <= num <= 50


# Rate limiting
class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int = 100, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str = "default") -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        self.calls[key] = [
            call_time
            for call_time in self.calls[key]
            if now - call_time < self.time_window
        ]

        if len(self.calls[key]) >= self.max_calls:
            return False

        self.calls[key].append(now)
        return True


# Global rate limiter
rate_limiter = RateLimiter(
    max_calls=int(os.getenv("MAX_CALLS_PER_MINUTE", "100")), time_window=60
)

# Initialize Seekr client and query tools
seekr_client = SeekrClient()
query_tools = SeekrQueryTools(seekr_client)

# Create FastMCP server
server = FastMCP(
    "mcp-server-seekr",
    instructions="This server provides web query and content extraction tools via Seekr API.",
)


@server.tool()
async def seekr_query(
    query: Annotated[
        str, Field(description="Query string to find relevant information")
    ],
    num: Annotated[
        int, Field(default=10, description="Number of query results to return (1-50)")
    ],
) -> str:
    """Query for information using Google query engine.

    This tool performs web queries to find current information, news, and diverse content.
    Use this for: current events, news, product information, troubleshooting,
    recent developments, and real-time information.

    After getting query results, use seekr_prism to get detailed content from specific URLs.
    """

    # Rate limiting check
    if not rate_limiter.is_allowed("query"):
        error_result = {
            "error": "Rate limit exceeded. Please try again later.",
            "tool": "seekr_query",
            "retry_after": 60,
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)

    # Input validation
    if not validate_query_string(query):
        error_result = {
            "error": "Invalid query string. Query must be a non-empty string (max 500 characters) without special characters.",
            "tool": "seekr_query",
            "query": query,
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)

    if not validate_num_results(num):
        error_result = {
            "error": f"Invalid number of results '{num}'. Must be between 1 and 50.",
            "tool": "seekr_query",
            "query": query,
            "num": num,
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)

    # Always use google engine
    engine = "google"

    logger.info(f"Executing query: query='{query}', engine='{engine}', num={num}")

    try:
        result = await query_tools.query(query, engine, num=num)
        response = json.dumps(result, indent=2, ensure_ascii=False)
        logger.info(f"Query successful: {len(response)} characters returned")
        return response

    except Exception as e:
        logger.error(f"Query failed: {e}")
        error_result = {
            "error": str(e),
            "tool": "seekr_query",
            "query": query,
            "engine": engine,
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)


@server.tool()
async def seekr_prism(
    url: Annotated[
        str,
        Field(
            description="Valid HTTP/HTTPS URL to prism and extract text content from"
        ),
    ],
) -> str:
    """Prism and extract detailed text content from a specific webpage URL.

    Use this tool to get full content from URLs found in query results.
    This provides more detailed information than query snippets alone.
    """

    # Rate limiting check
    if not rate_limiter.is_allowed("prism"):
        error_result = {
            "error": "Rate limit exceeded. Please try again later.",
            "tool": "seekr_prism",
            "retry_after": 60,
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)

    # Input validation
    if not validate_url(url):
        error_result = {
            "error": "Invalid URL format. URL must be a valid HTTP/HTTPS URL.",
            "tool": "seekr_prism",
            "url": url,
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)

    logger.info(f"Prisming webpage: {url}")

    try:
        result = await query_tools.prism(url)

        # Return the raw JSON response from the API
        response = json.dumps(result, indent=2, ensure_ascii=False)
        logger.info(f"Prism completed: {len(response)} characters returned")
        return response

    except Exception as e:
        logger.error(f"Prism failed: {e}")
        error_result = {"error": str(e), "tool": "seekr_prism", "url": url}
        return json.dumps(error_result, indent=2, ensure_ascii=False)


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting MCP Seekr server...")

    try:
        logger.info("Starting server with stdio transport...")
        # Run as stdio server for MCP clients
        await server.run_stdio_async()

    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


def run():
    """Synchronous entry point for console scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
