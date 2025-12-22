#!/usr/bin/env python3
"""
Neron MCP Server - Secure memory retrieval server
"""

import logging
from datetime import datetime, date

from mcp.server import Server
from mcp.types import Tool, TextContent

import db_connector
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Server(config.MCP_SERVER_NAME)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_notes_per_day",
            description="Retrieve all notes for a specific day",
            inputSchema={
                "type": "object",
                "properties": {
                    "day": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format"
                    }
                },
                "required": ["day"]
            }
        ),
        Tool(
            name="get_all_notes",
            description="Retrieve all notes from the database",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search",
            description="Semantic search using embeddings",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results (default: 5)",
                        "default": 5
                    }
                },
                "required": ["text"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_notes_per_day":
            day_str = arguments["day"]
            try:
                target_date = datetime.strptime(day_str, "%Y-%m-%d").date()
            except ValueError:
                return [TextContent(type="text", text=f"Invalid date format: {day_str}")]

            notes = db_connector.get_notes_by_day(target_date)
            if not notes:
                return [TextContent(type="text", text=f"No notes found for {day_str}")]

            result = [f"Found {len(notes)} note(s) for {day_str}:\n"]
            for i, (note_id, timestamp, text) in enumerate(notes, 1):
                result.append(f"\n{i}. [{timestamp.strftime('%H:%M:%S')}] {text}")

            return [TextContent(type="text", text="\n".join(result))]

        elif name == "get_all_notes":
            notes = db_connector.get_all_notes()
            if not notes:
                return [TextContent(type="text", text="No notes found")]

            result = [f"Found {len(notes)} note(s):\n"]
            for i, (note_id, timestamp, text) in enumerate(notes, 1):
                result.append(f"\n{i}. [{timestamp.strftime('%Y-%m-%d %H:%M')}] {text}")

            return [TextContent(type="text", text="\n".join(result))]

        elif name == "search":
            query_text = arguments["text"]
            top_k = arguments.get("top_k", 5)

            if top_k <= 0:
                return [TextContent(type="text", text="top_k must be positive")]

            results = db_connector.search_notes(query_text, top_k)
            if not results:
                return [TextContent(type="text", text=f"No results for: '{query_text}'")]

            result = [f"Found {len(results)} result(s) for '{query_text}':\n"]
            for i, (note_id, text, timestamp, similarity) in enumerate(results, 1):
                result.append(f"\n{i}. [{similarity*100:.1f}%] {timestamp.strftime('%Y-%m-%d')}")
                result.append(f"   {text}")

            return [TextContent(type="text", text="\n".join(result))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Tool error: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]
