"""
Database connector for Neron MCP Server.
Handles PostgreSQL operations with pgvector support.
"""

import logging
from datetime import datetime, date
from typing import List, Optional, Tuple
from psycopg2 import pool
import psycopg2
import voyageai

import config

# Setup logging
logger = logging.getLogger(__name__)

# Global connection pool
connection_pool: Optional[pool.ThreadedConnectionPool] = None

# Voyage AI client
voyage_client = None


def initialize_pool():
    """
    Initialize the PostgreSQL connection pool and Voyage AI client.
    Should be called once when the application starts.
    """
    global connection_pool, voyage_client

    try:
        # Initialize database connection pool
        connection_pool = pool.ThreadedConnectionPool(
            config.DB_MIN_CONNECTIONS,
            config.DB_MAX_CONNECTIONS,
            host=config.DB_HOST,
            port=config.DB_PORT,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        logger.info(f"Database connection pool initialized with {config.DB_MIN_CONNECTIONS}-{config.DB_MAX_CONNECTIONS} connections")

        # Initialize Voyage AI client
        voyage_client = voyageai.Client(api_key=config.VOYAGE_API_KEY)
        logger.info("Voyage AI client initialized")

    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
        raise


def get_connection():
    """Get a connection from the pool."""
    if connection_pool is None:
        raise RuntimeError("Connection pool not initialized. Call initialize_pool() first.")
    return connection_pool.getconn()


def return_connection(conn, close=False):
    """
    Return a connection to the pool.

    Args:
        conn: The connection to return
        close: If True, close the connection instead of returning it to the pool
    """
    if connection_pool is not None:
        if close:
            connection_pool.putconn(conn, close=True)
        else:
            connection_pool.putconn(conn)


def get_valid_connection(max_retries=3):
    """
    Get a valid connection from the pool with retry logic.
    Tests the connection before returning it.

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        A valid database connection

    Raises:
        Exception: If unable to get a valid connection after max_retries
    """
    for attempt in range(max_retries):
        conn = None
        try:
            conn = get_connection()

            # Test the connection with a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()

            # Connection is valid
            return conn

        except Exception as e:
            logger.warning(f"Connection validation failed (attempt {attempt + 1}/{max_retries}): {e}")

            # Close the bad connection
            if conn:
                try:
                    return_connection(conn, close=True)
                except Exception:
                    pass

            # If this was the last attempt, raise the error
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to get valid connection after {max_retries} attempts") from e

    # Should never reach here, but just in case
    raise RuntimeError("Failed to get valid connection")


def close_pool():
    """Close all connections in the pool."""
    global connection_pool
    if connection_pool is not None:
        connection_pool.closeall()
        logger.info("Database connection pool closed")


def get_notes_by_day(target_date: date) -> List[Tuple[int, datetime, str]]:
    """
    Get all notes for a specific day.

    Args:
        target_date: The date to retrieve notes for

    Returns:
        List of tuples: (id, timestamp, text)
    """
    conn = None
    close_conn = False
    try:
        conn = get_valid_connection()
        cursor = conn.cursor()

        # Query for notes on the specified day
        # We filter by date part of the timestamp
        cursor.execute(
            """
            SELECT id, timestamp, text
            FROM neron
            WHERE DATE(timestamp) = %s
            ORDER BY timestamp ASC;
            """,
            (target_date,)
        )

        results = cursor.fetchall()
        cursor.close()

        logger.info(f"Found {len(results)} notes for {target_date}")
        return results

    except Exception as e:
        logger.error(f"Error getting notes by day: {e}")
        close_conn = True
        raise
    finally:
        if conn:
            return_connection(conn, close=close_conn)


def get_all_notes() -> List[Tuple[int, datetime, str]]:
    """
    Get all notes from the database.

    Returns:
        List of tuples: (id, timestamp, text)
    """
    conn = None
    close_conn = False
    try:
        conn = get_valid_connection()
        cursor = conn.cursor()

        # Query all notes ordered by timestamp
        cursor.execute(
            """
            SELECT id, timestamp, text
            FROM neron
            ORDER BY timestamp DESC;
            """
        )

        results = cursor.fetchall()
        cursor.close()

        logger.info(f"Retrieved {len(results)} total notes")
        return results

    except Exception as e:
        logger.error(f"Error getting all notes: {e}")
        close_conn = True
        raise
    finally:
        if conn:
            return_connection(conn, close=close_conn)


def search_notes(query_text: str, top_k: int = 5) -> List[Tuple[int, str, datetime, float]]:
    """
    Perform semantic search on notes using embeddings.

    Args:
        query_text: The search query
        top_k: Number of top results to return

    Returns:
        List of tuples: (id, text, timestamp, similarity_score)
    """
    conn = None
    close_conn = False
    try:
        # Generate embedding for the query using Voyage AI
        logger.info(f"Generating embedding for query: '{query_text}'")
        result = voyage_client.embed(
            [query_text],
            model=config.VOYAGE_MODEL,
            input_type="query"
        )
        query_embedding = result.embeddings[0]

        # Validate embedding dimension
        if len(query_embedding) != config.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Embedding dimension mismatch: expected {config.EMBEDDING_DIMENSION}, "
                f"got {len(query_embedding)}"
            )

        # Query the database for similar notes
        conn = get_valid_connection()
        cursor = conn.cursor()

        # Use cosine similarity search
        # 1 - (embedding <=> query) converts distance to similarity score
        cursor.execute(
            """
            SELECT id, text, timestamp, 1 - (embedding <=> %s::vector) as similarity
            FROM neron
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
            """,
            (query_embedding, query_embedding, top_k)
        )

        results = cursor.fetchall()
        cursor.close()

        logger.info(f"Found {len(results)} similar notes")
        return results

    except Exception as e:
        logger.error(f"Error performing search: {e}")
        close_conn = True
        raise
    finally:
        if conn:
            return_connection(conn, close=close_conn)
