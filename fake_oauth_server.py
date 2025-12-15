#!/usr/bin/env python3
"""
Fake OAuth server - always returns same bearer token.
Implements all required OAuth 2.1 endpoints for Claude Desktop compatibility.
"""

import logging
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, RedirectResponse
from starlette.middleware.cors import CORSMiddleware

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FAKE_TOKEN = config.MCP_AUTH_TOKEN


async def oauth_metadata(request: Request):
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
    return JSONResponse({
        "issuer": f"https://{config.SERVER_DOMAIN}",
        "authorization_endpoint": f"https://{config.SERVER_DOMAIN}/authorize",
        "token_endpoint": f"https://{config.SERVER_DOMAIN}/token",
        "registration_endpoint": f"https://{config.SERVER_DOMAIN}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
    })


async def resource_metadata(request: Request):
    """Protected Resource Metadata (RFC 9728)."""
    return JSONResponse({
        "resource": f"https://{config.SERVER_DOMAIN}",
        "authorization_servers": [f"https://{config.SERVER_DOMAIN}"],
    })


async def register_client(request: Request):
    """Client registration (RFC 7591) - always succeeds."""
    body = await request.json()
    logger.info(f"Client registration: {body.get('client_name')}")

    return JSONResponse({
        "client_id": "neron-mcp",
        "client_secret": None,
        "redirect_uris": body.get("redirect_uris", []),
        "token_endpoint_auth_method": "none",
    })


async def authorize(request: Request):
    """Authorization endpoint - show fake login page."""
    params = dict(request.query_params)
    logger.info(f"Authorization request from client_id={params.get('client_id')}")

    # Build state for callback
    import urllib.parse
    state_params = urllib.parse.urlencode(params)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><title>Neron MCP - Authorize</title></head>
    <body style="font-family: sans-serif; max-width: 400px; margin: 50px auto;">
        <h1>Neron MCP</h1>
        <h2>Authorize Access</h2>
        <p><strong>Client:</strong> {params.get('client_id', 'Unknown')}</p>
        <p>This will grant access to your private notes.</p>
        <form method="POST" action="/authorize/callback">
            <input type="hidden" name="state_params" value="{state_params}">
            <button type="submit" style="padding: 10px 20px; font-size: 16px;">
                Authorize
            </button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(html)


async def authorize_callback(request: Request):
    """Handle authorization - always succeeds, returns fake code."""
    form = await request.form()
    state_params = form.get("state_params")

    # Parse original params
    import urllib.parse
    params = dict(urllib.parse.parse_qsl(state_params))

    redirect_uri = params.get("redirect_uri")
    state = params.get("state")

    # Return fake authorization code
    fake_code = "fake_auth_code_always_same"

    logger.info(f"Authorization granted, redirecting to {redirect_uri}")
    return RedirectResponse(
        f"{redirect_uri}?code={fake_code}&state={state}",
        status_code=303  # 303 See Other - converts POST to GET
    )


async def token_exchange(request: Request):
    """Token endpoint - always returns the same bearer token."""
    form = await request.form()
    logger.info(f"Token exchange for code={form.get('code')}")

    # Always return the same token from .env
    return JSONResponse({
        "access_token": FAKE_TOKEN,
        "token_type": "Bearer",
        "expires_in": 315360000,  # 10 years
        "scope": "user",
    })


app = Starlette(
    routes=[
        Route("/.well-known/oauth-authorization-server", oauth_metadata, methods=["GET"]),
        Route("/.well-known/oauth-protected-resource", resource_metadata, methods=["GET"]),
        Route("/register", register_client, methods=["POST", "OPTIONS"]),
        Route("/authorize", authorize, methods=["GET"]),
        Route("/authorize/callback", authorize_callback, methods=["POST"]),
        Route("/token", token_exchange, methods=["POST", "OPTIONS"]),
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins since this is a fake OAuth for personal use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Fake OAuth Server at https://{config.SERVER_DOMAIN}")
    logger.info(f"All flows will return token: {FAKE_TOKEN[:20]}...")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
