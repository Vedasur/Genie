"""One-time local OAuth for Gmail read-only access.

Run this on your machine (not in Docker) after placing Google Cloud Desktop
OAuth client secrets at ``credentials.json``:

    cd google_mcp
    uv run python gmail_auth.py

A browser window opens for consent. On success, ``secrets/token.json`` is
written and can be mounted into the google_mcp container.
"""

from __future__ import annotations

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

HERE = Path(__file__).resolve().parent
CREDENTIALS_PATH = HERE / "credentials.json"
TOKEN_PATH = HERE / "secrets" / "token.json"


def main() -> None:
    if not CREDENTIALS_PATH.is_file():
        raise SystemExit(
            f"Missing {CREDENTIALS_PATH}. Download a Desktop OAuth client JSON "
            "from Google Cloud Console and save it as credentials.json."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    creds = flow.run_local_server(port=0)

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print(f"Saved {TOKEN_PATH}")


if __name__ == "__main__":
    main()
