"""Core tools: time, timers, web search, notes."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger

from app.tools.registry import Tool, registry


async def get_current_time(timezone: str = "local") -> dict[str, Any]:
    """Get the current time."""
    now = datetime.now()
    return {
        "time": now.isoformat(),
        "formatted": now.strftime("%I:%M %p"),
        "date": now.strftime("%Y-%m-%d"),
        "timezone": timezone,
    }


def set_timer(duration_minutes: int = 1, label: str = "Timer") -> dict[str, Any]:
    """Set a timer."""
    return {
        "status": "set",
        "duration_minutes": duration_minutes,
        "label": label,
        "expires_at": (datetime.now() + timedelta(minutes=duration_minutes)).isoformat(),
    }


async def web_search(query: str, num_results: int = 5) -> dict[str, Any]:
    """Search the web."""
    # Mock implementation - in production would use a real search API
    return {
        "query": query,
        "results": [
            {"title": f"Result {i+1} for {query}", "url": f"https://example.com/{i}", "snippet": f"Sample result {i+1}"}
            for i in range(min(num_results, 3))
        ],
    }


NOTES_FILE = Path(__file__).parent.parent.parent / "notes.json"


def _load_notes() -> list[dict[str, Any]]:
    if NOTES_FILE.exists():
        try:
            return json.loads(NOTES_FILE.read_text())
        except Exception:
            return []
    return []


def _save_notes(notes: list[dict[str, Any]]):
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


async def create_note(content: str, title: str = "") -> dict[str, Any]:
    """Create a note."""
    notes = _load_notes()
    note = {
        "id": len(notes) + 1,
        "title": title or content[:30],
        "content": content,
        "created_at": datetime.now().isoformat(),
    }
    notes.append(note)
    _save_notes(notes)
    return {"status": "created", "note": note}


async def list_notes() -> dict[str, Any]:
    """List all notes."""
    notes = _load_notes()
    return {"notes": notes, "count": len(notes)}


async def search_notes(query: str) -> dict[str, Any]:
    """Search notes."""
    notes = _load_notes()
    results = [n for n in notes if query.lower() in n.get("content", "").lower() or query.lower() in n.get("title", "").lower()]
    return {"query": query, "results": results, "count": len(results)}


def register_core_tools():
    registry.register(Tool(
        name="get_current_time",
        description="Get the current time and date",
        parameters={"properties": {"timezone": {"type": "string"}}, "required": []},
        function=get_current_time,
    ))
    registry.register(Tool(
        name="set_timer",
        description="Set a timer for a specified duration",
        parameters={"properties": {"duration_minutes": {"type": "integer"}, "label": {"type": "string"}}, "required": ["duration_minutes"]},
        function=set_timer,
    ))
    registry.register(Tool(
        name="web_search",
        description="Search the web for information",
        parameters={"properties": {"query": {"type": "string"}, "num_results": {"type": "integer"}}, "required": ["query"]},
        function=web_search,
    ))
    registry.register(Tool(
        name="create_note",
        description="Create a note",
        parameters={"properties": {"content": {"type": "string"}, "title": {"type": "string"}}, "required": ["content"]},
        function=create_note,
    ))
    registry.register(Tool(
        name="list_notes",
        description="List all notes",
        parameters={"properties": {}, "required": []},
        function=list_notes,
    ))
    registry.register(Tool(
        name="search_notes",
        description="Search notes",
        parameters={"properties": {"query": {"type": "string"}}, "required": ["query"]},
        function=search_notes,
    ))


register_core_tools()
