"""MCP server setup.

fastmcp does the heavy lifting:
- defines the MCP protocol over HTTP
- generates JSON Schema from your tool function signatures
- handles tool dispatch when an AI client calls one

Two auth modes are selected via the AUTH_MODE env var:

- "bearer" — simplest. AI client sends `Authorization: Bearer <token>` and we
  check it against MCP_API_KEY. Use for: local testing, Codex/Cursor, your own
  scripts.

- "oauth"  — production. fastmcp's OAuth provider implements Dynamic Client
  Registration (DCR), which is what Claude.ai Custom Connectors require to
  register themselves without you hand-creating client_id/client_secret pairs
  per consumer. Use for: Claude.ai.

This file deliberately keeps the two modes side-by-side so a learner can read
the whole auth surface in one screen.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
# BearerAuthProvider is deprecated in fastmcp 2.x but still works for our simple
# shared-secret case. When fastmcp 3.x lands and removes it, migrate this branch
# to either JWTVerifier (issuing the AI client a JWT) or a custom auth middleware
# that checks the Authorization header against MCP_API_KEY directly.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from fastmcp.server.auth import BearerAuthProvider

# --- Config (resolved at import time so failures surface at startup) -----------
AUTH_MODE = os.getenv("AUTH_MODE", "bearer").lower()
NOTES_DIR = Path(os.getenv("NOTES_DIR", "./notes")).resolve()

if not NOTES_DIR.is_dir():
    raise RuntimeError(
        f"NOTES_DIR={NOTES_DIR} is not a directory. Set NOTES_DIR in your environment "
        f"or create the directory."
    )

# --- Auth provider selection --------------------------------------------------
if AUTH_MODE == "bearer":
    api_key = os.getenv("MCP_API_KEY", "")
    if not api_key or api_key == "replace-me-with-a-long-random-string":
        raise RuntimeError(
            "AUTH_MODE=bearer requires MCP_API_KEY to be set to a real secret. "
            "Generate one with: openssl rand -hex 32"
        )
    auth = BearerAuthProvider(
        # The provider treats this as the canonical bearer; any other value 401s.
        # Production: rotate by re-deploying with a new MCP_API_KEY.
        public_key=api_key,
    )

elif AUTH_MODE == "oauth":
    issuer = os.getenv("OAUTH_ISSUER_URL", "")
    jwt_secret = os.getenv("OAUTH_JWT_SECRET", "")
    if not issuer or not jwt_secret:
        raise RuntimeError(
            "AUTH_MODE=oauth requires OAUTH_ISSUER_URL and OAUTH_JWT_SECRET. "
            "See SETUP.md §'Adding OAuth for Claude.ai' for the full setup."
        )
    # fastmcp's JWTVerifier validates incoming bearer JWTs against the issuer.
    # The OAuth + DCR endpoints (/.well-known/oauth-authorization-server,
    # /register, /authorize, /token) are wired below by FastMCP when an
    # auth provider is attached.
    auth = JWTVerifier(
        public_key=jwt_secret,
        issuer=issuer,
        audience=issuer,
    )

else:
    raise RuntimeError(f"Unknown AUTH_MODE={AUTH_MODE!r}; expected 'bearer' or 'oauth'.")

# --- The MCP server ------------------------------------------------------------
mcp = FastMCP(
    name="mcp-gateway-starter",
    instructions=(
        "A teaching template for an MCP gateway. Wraps a folder of markdown notes "
        "and exposes list_notes, read_note, search_notes."
    ),
    auth=auth,
)

# Register tools — importing the module triggers the @mcp.tool decorators.
from app import tools  # noqa: E402, F401
