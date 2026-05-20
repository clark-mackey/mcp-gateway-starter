# Auth modes — bearer vs OAuth

This gateway supports two auth modes. Pick based on which AI client you're connecting from.

## Bearer (default)

The AI client sends `Authorization: Bearer <token>` with every request. The gateway compares the token against `MCP_API_KEY`. Match → allow. Mismatch → 401.

**When to use:**
- Local development with MCP Inspector
- Codex CLI, Cursor, Claude Code — anything that lets you paste in a bearer token
- Your own scripts hitting the MCP endpoint via `httpx` or similar
- Multi-tenant if you assign one key per tenant (simple but not granular)

**Limitation:** every client shares the same key. Rotation requires a re-deploy with a new `MCP_API_KEY`.

## OAuth + DCR

OAuth 2.0 with Dynamic Client Registration. The AI client registers itself at runtime (via `/register`), gets a `client_id` and `client_secret`, then goes through an authorization flow to receive a JWT. The JWT is what's sent on subsequent requests.

**When to use:**
- Claude.ai Custom Connectors (this is what Claude.ai requires)
- Any client that does the full OAuth dance
- Multi-tenant with per-client credentials and revocable access

**Cost:** more setup — see SETUP.md §Adding OAuth for Claude.ai. The trade-off is real granularity (revoke one consumer without affecting others) and Claude.ai compatibility.

## Recommendation

**Start with bearer.** Get the gateway running, see the tools work in MCP Inspector. Then add OAuth when you're ready to wire Claude.ai.
