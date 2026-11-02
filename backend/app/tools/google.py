"""Google Calendar and Gmail tools via API (with MCP support structure)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from loguru import logger

from app.tools.registry import Tool, registry


async def list_calendar_events(days: int = 7) -> dict[str, Any]:
    """List upcoming calendar events."""
    # Placeholder - would integrate with Google Calendar API
    return {
        "events": [
            {"title": "Team Meeting", "time": "2024-01-01T10:00:00", "duration": "1h"},
            {"title": "Lunch", "time": "2024-01-01T12:30:00", "duration": "30m"},
        ],
        "days": days,
    }


async def create_calendar_event(title: str, start_time: str, duration_minutes: int = 60) -> dict[str, Any]:
    """Create a calendar event (requires confirmation)."""
    return {
        "status": "created",
        "event": {"title": title, "start_time": start_time, "duration_minutes": duration_minutes},
    }


async def list_emails(max_results: int = 10) -> dict[str, Any]:
    """List recent emails."""
    # Placeholder
    return {
        "emails": [
            {"from": "alice@example.com", "subject": "Meeting Tomorrow", "snippet": "Hi, just confirming..."},
            {"from": "bob@example.com", "subject": "Project Update", "snippet": "The latest build..."},
        ],
        "max_results": max_results,
    }


async def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email (requires confirmation)."""
    return {
        "status": "sent",
        "to": to,
        "subject": subject,
    }


def register_google_tools():
    registry.register(Tool(
        name="list_calendar_events",
        description="List upcoming Google Calendar events",
        parameters={"properties": {"days": {"type": "integer"}}, "required": []},
        function=list_calendar_events,
    ))
    registry.register(Tool(
        name="create_calendar_event",
        description="Create a Google Calendar event",
        parameters={"properties": {"title": {"type": "string"}, "start_time": {"type": "string"}, "duration_minutes": {"type": "integer"}}, "required": ["title", "start_time"]},
        function=create_calendar_event,
        requires_confirmation=True,
    ))
    registry.register(Tool(
        name="list_emails",
        description="List recent Gmail messages",
        parameters={"properties": {"max_results": {"type": "integer"}}, "required": []},
        function=list_emails,
    ))
    registry.register(Tool(
        name="send_email",
        description="Send an email via Gmail",
        parameters={"properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]},
        function=send_email,
        requires_confirmation=True,
    ))


register_google_tools()
