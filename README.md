# Neron MCP Server

Secure MCP server providing semantic search and retrieval over personal notes stored in PostgreSQL with pgvector embeddings.

## Goal

Provide authenticated access to private note retrieval via Model Context Protocol (MCP) using streamable HTTP transport. The server is designed to be secure-by-default: all endpoints require bearer token authentication and data is only accessible via HTTPS.

## Features

- **Semantic Search**: Query notes using natural language via Voyage AI embeddings
- **Date-based Retrieval**: Get all notes for a specific day
- **Full Access**: Retrieve all notes from the database
- **Secure**: Bearer token authentication required for all requests
- **Production Ready**: HTTPS with automatic Let's Encrypt certificates

## Architecture

```
Client → HTTPS (mcp.neron.guru) → Caddy → HTTP (localhost:8000) → MCP Server → PostgreSQL + pgvector
```

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension
- Caddy web server
- Voyage AI API key

### Setup

1. **Clone and configure**:
```bash
cd /path/to/Neron-MCP
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Install Caddy**:
```bash
sudo snap install caddy
```

4. **Configure Caddy**:
```bash
sudo cp Caddyfile /etc/caddy/Caddyfile
sudo systemctl restart caddy
```

5. **Setup systemd service**:
```bash
sudo cp neron-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable neron-mcp
sudo systemctl start neron-mcp
```

## Configuration

All configuration is done via environment variables in `.env`:

### Required Variables

- `MCP_AUTH_TOKEN` - Bearer token for authentication
- `VOYAGE_API_KEY` - Voyage AI API key for embeddings
- `DB_PASSWORD` - PostgreSQL password

### Optional Variables

- `MCP_SERVER_NAME` - Server name (default: "neron-mcp")
- `VOYAGE_MODEL` - Embedding model (default: "voyage-3-large")
- `EMBEDDING_DIMENSION` - Vector dimension (default: 1024)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` - PostgreSQL connection
- `DB_MIN_CONNECTIONS`, `DB_MAX_CONNECTIONS` - Connection pool settings

## Usage

### Connecting

**Server URL**: `https://mcp.neron.guru`

**Authentication**: Bearer token in `Authorization` header

```bash
Authorization: Bearer <your-token-from-env>
```

### Available Tools

#### 1. get_notes_per_day

Retrieve all notes for a specific day.

```json
{
  "day": "2025-12-14"
}
```

#### 2. get_all_notes

Retrieve all notes from the database. No parameters required.

#### 3. search

Perform semantic search using embeddings.

```json
{
  "text": "meeting notes about project",
  "top_k": 5
}
```

## Database Schema

```sql
CREATE TABLE neron (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    text TEXT NOT NULL,
    embedding vector(1024) NOT NULL
);
```

- Database: `postgres`
- Table: `neron`
- Shared with Neron-Bot for data input

## Project Structure

```
.
├── server.py           # MCP server with tool handlers
├── http_server.py      # HTTP wrapper with authentication
├── db_connector.py     # PostgreSQL and Voyage AI integration
├── config.py           # Configuration loader
├── requirements.txt    # Python dependencies
├── Caddyfile          # HTTPS reverse proxy configuration
├── .env               # Environment variables (not in git)
└── .env.example       # Environment template
```

## Security

- All endpoints require bearer token authentication
- HTTPS enforced via Caddy with Let's Encrypt
- Database credentials stored in environment variables
- Private data - no unauthenticated access permitted

## Monitoring

### Check server status

```bash
sudo systemctl status neron-mcp
```

### View logs

```bash
sudo journalctl -u neron-mcp -f
```

### Test authentication

```bash
# Should return 401 Unauthorized
curl https://mcp.neron.guru

# Should work with token
curl -H "Authorization: Bearer your-token-here" https://mcp.neron.guru
```

## Troubleshooting

### Server won't start

1. Check configuration: `python config.py`
2. Check database: `sudo -u postgres psql -d postgres -c "SELECT COUNT(*) FROM neron;"`
3. Check logs: `sudo journalctl -u neron-mcp -n 50`

### Authentication failures

1. Verify token in `.env` matches client token
2. Check `Authorization` header format: `Bearer <token>`
3. Review server logs for authentication attempts

### HTTPS issues

1. Check Caddy: `sudo systemctl status caddy`
2. Validate Caddyfile: `sudo caddy validate --config /etc/caddy/Caddyfile`
3. Check DNS: `dig mcp.neron.guru`

## License

Private project.

## Dependencies

- `mcp>=1.0.0` - Model Context Protocol SDK
- `voyageai>=0.2.3` - Voyage AI embeddings
- `psycopg2-binary>=2.9.10` - PostgreSQL adapter
- `python-dotenv>=1.0.1` - Environment variable management
- `starlette` - ASGI framework
- `uvicorn` - ASGI server
