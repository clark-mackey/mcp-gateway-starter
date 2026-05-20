"""FastAPI entry point.

This file does three things:
1. Loads the .env file (for local dev — Railway injects env vars directly).
2. Wraps the fastmcp server in a FastAPI app.
3. Adds a /health endpoint so Railway's health check passes.

The MCP protocol is mounted at /mcp/ — that's the URL you give Claude.ai or
any other MCP client.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI

# Load .env BEFORE importing app.server (which reads env vars at import time).
load_dotenv()

from app.server import mcp, AUTH_MODE  # noqa: E402

# fastmcp 2.x: get the underlying HTTP app to mount under our FastAPI.
mcp_app = mcp.http_app(path="/mcp/")

# Pass the MCP app's lifespan into FastAPI so MCP's startup/shutdown hooks fire.
app = FastAPI(
    title="MCP Gateway Starter",
    description="A teaching template wrapping a markdown vault as an MCP gateway.",
    version="0.1.0",
    lifespan=mcp_app.lifespan,
)


@app.get("/health")
def health() -> dict:
    """Liveness probe. Railway's healthcheck hits this."""
    return {"status": "ok", "auth_mode": AUTH_MODE}


# Mount the MCP server. Everything under /mcp/ is handled by fastmcp.
app.mount("/", mcp_app)
