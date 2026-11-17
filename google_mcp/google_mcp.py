"""Google MCP server — Gmail read-only tools."""

from __future__ import annotations

import base64
import os
from datetime import date, datetime, timezone
from typing import Annotated

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger
from mcp.server.mcpserver import Context, MCPServer
from pydantic import BaseModel, Field

from utils.logger import setup_logging

setup_logging()

HOST = os.environ.get("MCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("MCP_PORT", "8081"))
BODY_MAX_CHARS = 5000

mcp = MCPServer("Google service", version=os.environ.get("SERVICE_VERSION", "0.1.0"))


class EmailMessage(BaseModel):
    """One received email with truncated plain-text body."""

    id: str = Field(description="Gmail message id.")
    sender: str = Field(description="From header value.")
    subject: str = Field(description="Subject header value.")
    date: str = Field(description="Date header value.")
    snippet: str = Field(description="Short Gmail snippet.")
    body: str = Field(description="Plain-text body, truncated for LLM context.")


def _gmail_from_ctx(ctx: Context):
    """Build a Gmail client from the caller's OAuth access token (sent by LibreChat)."""
    auth = (ctx.headers or {}).get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise ValueError("Missing Google OAuth token; connect Gmail in LibreChat first.")
    creds = Credentials(token=auth[7:])
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _header(headers: list[dict], name: str) -> str:
    return next(
        (h["value"] for h in headers if h.get("name", "").lower() == name.lower()),
        "",
    )


def _extract_text(payload: dict) -> str:
    """Walk the MIME tree and return the first text/plain part."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        raw = base64.urlsafe_b64decode(payload["body"]["data"])
        return raw.decode("utf-8", "replace")
    for part in payload.get("parts") or []:
        text = _extract_text(part)
        if text:
            return text
    return ""


@mcp.tool()
def read_recent_emails(
    ctx: Context,
    since_date: Annotated[
        date,
        Field(
            description=(
                "ISO date YYYY-MM-DD. Return emails received from this date "
                "(00:00 UTC) up to now."
            )
        ),
    ],
    max_results: Annotated[
        int,
        Field(ge=1, le=50, description="Maximum number of emails to return."),
    ] = 20,
) -> list[EmailMessage]:
    """Read recent received inbox emails from ``since_date`` up to now.

    Use this when the user asks what arrived in their inbox on or after a date.
    Returns sender, subject, date, snippet, and a truncated plain-text body.
    Does not send, delete, or modify mail.

    Args:
        since_date: Inclusive start date (UTC midnight) in YYYY-MM-DD.
        max_results: Cap on how many messages to fetch (1–50).

    Returns:
        A list of EmailMessage objects, newest first. Empty if none match.

    Example:
        read_recent_emails(since_date=date(2026, 11, 1), max_results=10)
    """
    epoch = int(datetime(since_date.year, since_date.month, since_date.day, tzinfo=timezone.utc).timestamp())
    query = f"in:inbox after:{epoch}"
    svc = _gmail_from_ctx(ctx)

    try:
        listing = (
            svc.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
    except Exception:
        logger.exception("Gmail messages.list failed for query={}", query)
        raise

    messages = listing.get("messages") or []
    if not messages:
        return []

    out: list[EmailMessage] = []
    for item in messages:
        try:
            msg = (
                svc.users()
                .messages()
                .get(userId="me", id=item["id"], format="full")
                .execute()
            )
        except Exception:
            logger.exception("Gmail messages.get failed for id={}", item.get("id"))
            raise

        headers = msg.get("payload", {}).get("headers", [])
        body = _extract_text(msg.get("payload", {}))[:BODY_MAX_CHARS]
        out.append(
            EmailMessage(
                id=msg["id"],
                sender=_header(headers, "From"),
                subject=_header(headers, "Subject"),
                date=_header(headers, "Date"),
                snippet=msg.get("snippet", ""),
                body=body,
            )
        )

    logger.info("read_recent_emails since={} returned={}", since_date.isoformat(), len(out))
    return out


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host=HOST, port=PORT)
