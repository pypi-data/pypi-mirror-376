#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="mcp-server-seekr",
    description="MCP server for web search and content extraction via Seekr API",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Danilo Falcão",
    author_email="danilo@falcao.org",
    license="MIT",
    license_files=["LICENSE"],
    keywords=[
        "mcp",
        "seekr",
        "search",
        "scrape",
        "claude",
        "claude-desktop",
        "modelcontextprotocol",
    ],
    url="https://github.com/seekr-sh/mcp-server-seekr",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "fastmcp>=0.1.0",
        "httpx>=0.27.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-server-seekr=mcp_server_seekr.main:run",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
