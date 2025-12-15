# Neron MCP Server

Secure MCP server with OAuth 2.1 authentication for Claude Desktop and MCP clients.

## Architecture

```
Client (Claude Desktop) → HTTPS → Caddy Reverse Proxy
                                      ↓
                     ┌────────────────┴────────────────┐
                     ↓                                 ↓
        OAuth Server (port 8001)          MCP Server (port 8000)
        - /authorize                       - Token validation
        - /token                           - MCP tools
        - /register                        - Database queries
        - Discovery endpoints
```

## Features

- **OAuth 2.1 Authorization**: Full OAuth flow for Claude Desktop
- **Semantic Search**: Query notes using Voyage AI embeddings
- **Date-based Retrieval**: Get notes for specific days
- **HTTPS**: Automatic Let's Encrypt certificates
- **Token-based Auth**: Bearer token validation

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector
- Caddy web server
- Voyage AI API key

### Setup

1. **Install dependencies**:
```bash
cd /home/Neron-MCP
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment** (`.env` file):
   - `MCP_AUTH_TOKEN`: Bearer token (returned by OAuth flow)
   - `VOYAGE_API_KEY`: Voyage AI API key
   - `DB_PASSWORD`: PostgreSQL password
   - `SERVER_DOMAIN`: Your domain (e.g., mcp.neron.guru)

3. **Install services**:
```bash
# OAuth server
sudo cp neron-oauth.service /etc/systemd/system/
sudo systemctl enable neron-oauth
sudo systemctl start neron-oauth

# MCP server
sudo cp neron-mcp.service /etc/systemd/system/
sudo systemctl enable neron-mcp
sudo systemctl start neron-mcp

# Caddy
sudo cp Caddyfile /etc/caddy/Caddyfile
sudo systemctl restart caddy
```

## OAuth Flow

The server implements a **simplified OAuth 2.1 flow**:

1. Client discovers OAuth server via `/.well-known/oauth-authorization-server`
2. Client registers via `/register` endpoint
3. Client redirects to `/authorize` for user consent
4. User clicks "Authorize" button
5. Server redirects back with authorization code
6. Client exchanges code for bearer token at `/token`
7. Client uses token for all MCP requests

**Note**: The OAuth server always returns the same bearer token from `.env` for simplicity. After authorizing all devices, you can shut down the OAuth server (port 8001) - the MCP server will continue validating tokens.

**Technical details**:
- Uses 303 See Other redirect to convert POST → GET for OAuth callback
- CORS enabled for cross-origin token exchange
- PKCE support with S256 code challenge method

## Connecting from Claude Desktop

1. Add server configuration to Claude Desktop
2. Claude will open browser for authorization
3. Click "Authorize" in the browser
4. Claude Desktop receives token automatically
5. Start using the MCP tools

**Server URL**: `https://mcp.neron.guru`

## Available Tools

### 1. get_notes_per_day
```json
{"day": "2025-12-14"}
```

### 2. get_all_notes
No parameters required.

### 3. search
```json
{"text": "meeting notes", "top_k": 5}
```

## Database

Connects to existing PostgreSQL database:
- **Database**: postgres
- **Table**: neron
- **Vector dimension**: 1024 (voyage-3-large)

Shared with Neron-Bot for data input.

## Monitoring

### Check services
```bash
sudo systemctl status neron-oauth
sudo systemctl status neron-mcp
sudo systemctl status caddy
```

### View logs
```bash
# OAuth server
sudo journalctl -u neron-oauth -f

# MCP server
sudo journalctl -u neron-mcp -f

# Caddy
sudo tail -f /var/log/caddy/mcp-neron.log
```

### Test endpoints
```bash
# OAuth discovery
curl https://mcp.neron.guru/.well-known/oauth-authorization-server

# Protected resource metadata
curl https://mcp.neron.guru/.well-known/oauth-protected-resource

# MCP endpoint (requires token)
curl -H "Authorization: Bearer <token>" https://mcp.neron.guru
```

## Security

- ✅ OAuth 2.1 with PKCE (S256 code challenge)
- ✅ HTTPS only (TLS 1.2+)
- ✅ Bearer token validation on every request
- ✅ CORS-compliant OAuth implementation
- ✅ No passwords stored (single-user auth)
- ✅ Can disable OAuth server after initial setup
- ✅ Protected resource metadata (RFC 9728)

## Shutting Down OAuth Server

After authorizing all your devices:

```bash
sudo systemctl stop neron-oauth
sudo systemctl disable neron-oauth
```

The MCP server will continue working with existing tokens. Re-enable OAuth server only when adding new devices:

```bash
sudo systemctl enable neron-oauth
sudo systemctl start neron-oauth
```

## Files

```
├── server.py              # MCP server core (3 tools)
├── http_server.py         # MCP HTTP wrapper with token validation
├── fake_oauth_server.py   # OAuth 2.1 authorization server
├── db_connector.py        # Database operations
├── config.py              # Configuration
├── requirements.txt       # Dependencies
├── Caddyfile             # HTTPS routing
├── neron-mcp.service     # MCP systemd service
├── neron-oauth.service   # OAuth systemd service
└── .env                  # Secrets (not in git)
```

## Troubleshooting

### OAuth server not responding
```bash
sudo systemctl status neron-oauth
sudo journalctl -u neron-oauth -n 50
```

### MCP server connection issues
```bash
# Check if service is running
sudo systemctl status neron-mcp

# Verify token in .env matches what Claude has
grep MCP_AUTH_TOKEN /home/Neron-MCP/.env

# Test token manually
curl -H "Authorization: Bearer YOUR_TOKEN" https://mcp.neron.guru
```

### Claude Desktop authorization fails
1. Make sure OAuth server is running: `sudo systemctl start neron-oauth`
2. Check browser console for errors
3. Verify domain is accessible: `curl https://mcp.neron.guru/.well-known/oauth-authorization-server`
4. Review Caddy logs: `sudo tail -f /var/log/caddy/mcp-neron.log`

## License

Private project.
