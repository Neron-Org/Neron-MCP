#!/usr/bin/env python3
"""
Neron MCP HTTP Server - Validates bearer tokens from fake OAuth server.
"""

import logging
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
from starlette.requests import Request
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

import config
import db_connector
from server import app as mcp_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session_manager = None


async def verify_token(request: Request) -> bool:
    """Verify bearer token matches the hardcoded one."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    token = auth_header[7:]
    return token == config.MCP_AUTH_TOKEN


async def handle_mcp(request: Request):
    """Handle MCP requests with token validation."""
    if not await verify_token(request):
        logger.warning(f"Invalid token from {request.client}")
        return Response(
            content="Unauthorized",
            status_code=401,
            headers={
                "WWW-Authenticate": f'Bearer realm="mcp", resource_metadata_url="https://{config.SERVER_DOMAIN}/.well-known/oauth-protected-resource"'
            },
        )

    logger.info(f"Authenticated request from {request.client}")
    return await session_manager.handle_request(request.scope, request.receive, request._send)


@asynccontextmanager
async def lifespan(app):
    """Manage application lifespan."""
    global session_manager

    logger.info("Initializing database...")
    db_connector.initialize_pool()

    logger.info("Initializing MCP session manager...")
    session_manager = StreamableHTTPSessionManager(mcp_app)

    async with session_manager.run():
        logger.info(f"MCP server ready: {config.MCP_SERVER_NAME}")
        yield

    logger.info("Closing database...")
    db_connector.close_pool()


http_app = Starlette(
    routes=[Route("/", handle_mcp, methods=["GET", "POST"])],
    lifespan=lifespan,
)


if __name__ == "__main__":
    import uvicorn

    config.validate_config()
    logger.info(f"Starting {config.MCP_SERVER_NAME} on port 8000")
    logger.info("Token validation enabled")

    uvicorn.run(http_app, host="0.0.0.0", port=8000, log_level="info")
