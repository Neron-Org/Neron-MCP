"""
Configuration for Neron MCP Server
"""

import os
from dotenv import load_dotenv

load_dotenv()

# MCP Server
MCP_SERVER_NAME = os.getenv('MCP_SERVER_NAME', 'neron-mcp')
MCP_AUTH_TOKEN = os.getenv('MCP_AUTH_TOKEN')

# Voyage AI
VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')
VOYAGE_MODEL = os.getenv('VOYAGE_MODEL', 'voyage-3-large')
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '1024'))

# PostgreSQL
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'postgres')
DB_USER = os.getenv('DB_USER', 'neron_bot')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_MIN_CONNECTIONS = int(os.getenv('DB_MIN_CONNECTIONS', '2'))
DB_MAX_CONNECTIONS = int(os.getenv('DB_MAX_CONNECTIONS', '10'))


def validate_config():
    """Validate required environment variables."""
    required = {
        'MCP_AUTH_TOKEN': MCP_AUTH_TOKEN,
        'VOYAGE_API_KEY': VOYAGE_API_KEY,
        'DB_PASSWORD': DB_PASSWORD,
    }

    missing = [k for k, v in required.items() if not v]

    if missing:
        raise ValueError(f"Missing required config: {', '.join(missing)}")


if __name__ == '__main__':
    try:
        validate_config()
        print("✓ Configuration valid")
    except ValueError as e:
        print(f"✗ {e}")
