# mcp-gateway-starter

A minimal, teachable starter for an **MCP gateway** — a service that lets AI clients (Claude.ai, Codex, Cursor) call your tools and read your knowledge.

This template wraps a folder of markdown notes and exposes three tools: `list_notes`, `read_note`, `search_notes`. You can swap the markdown layer for any data source (Postgres, Notion, your CRM, your CSV files) by replacing **one file** — `app/tools.py`.

**~250 lines of Python. Deploys anywhere Python runs — Render, Railway, Cloud Run — in about 10 minutes. Two auth modes: bearer for local dev, OAuth for Claude.ai Custom Connectors.**

> **Prefer JavaScript?** Cloudflare's [`remote-mcp-authless` template](https://developers.cloudflare.com/agents/guides/remote-mcp-server/) is the slickest TS/Workers path — `npm create cloudflare@latest` and you're live. This repo is the **Python** path: readable code, OAuth+DCR in the open, swap one file to point at your data.

---

## What you'll have after deploying

- An HTTPS URL like `https://your-gateway.up.railway.app`
- A working MCP endpoint at `https://your-gateway.up.railway.app/mcp/`
- Three callable tools your AI client can use
- Auth: bearer token for local testing; OAuth + DCR for Claude.ai

---

## Quickstart (local — 5 minutes)

```bash
# 1. Clone
gh repo clone clark-mackey/mcp-gateway-starter
cd mcp-gateway-starter

# 2. Install (uv recommended; pip works too)
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env — set MCP_API_KEY to anything you want for local testing

# 4. Run
uvicorn app.main:app --reload --port 8000

# 5. Test from MCP Inspector
#    Open https://modelcontextprotocol.io/inspector
#    Server URL: http://localhost:8000/mcp/
#    Auth: Bearer <whatever you set MCP_API_KEY to>
#    Try calling list_notes() — should return the sample notes
```

---

## Deploy

Three documented paths. Pick one — the gateway itself is identical on all of them.

### Option 1 — Render (recommended for most people)

Render is the easiest path: same one-click GitHub flow as Railway, **real free tier, no credit card required**, and Render auto-detects FastAPI.

1. Push this repo to your own GitHub.
2. At [render.com](https://render.com), **New → Web Service → connect your repo**.
3. Build command: `pip install -r requirements.txt`. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Environment variables: `AUTH_MODE=bearer` and `MCP_API_KEY=<a random 64-char string>`.
5. Deploy. You get an HTTPS URL like `https://your-gateway.onrender.com`.

Heads up: Render's free tier spins down after ~15 minutes idle (cold start ~60 seconds on next request). Fine for testing; upgrade to the $7/month Starter if you connect this to Claude.ai for production use — connector handshakes will time out on a cold start.

### Option 2 — Railway

```bash
npm i -g @railway/cli && railway login
railway init                                                    # create project
railway up                                                      # deploy
railway variables --set AUTH_MODE=bearer
railway variables --set "MCP_API_KEY=$(openssl rand -hex 32)"
railway domain                                                  # public URL
```

Railway's hobby tier runs ~$5/month and doesn't sleep — worth it once you're using the gateway for real. Full walkthrough in [SETUP.md](SETUP.md).

### Option 3 — Google Cloud Run

Generous free tier (2M requests/month, scale-to-zero). One command from the repo root:

```bash
gcloud run deploy mcp-gateway --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars AUTH_MODE=bearer,MCP_API_KEY=$(openssl rand -hex 32)
```

Requires a GCP account with billing enabled (you won't be charged at low traffic, but Google requires a card on file).

### Verifying any deploy

```bash
curl https://<your-url>/health
#    -> {"status":"ok","auth_mode":"bearer"}
```

Your MCP endpoint is `https://<your-url>/mcp/`. Any MCP client with `Authorization: Bearer <your MCP_API_KEY>` can use it.

For **Claude.ai Custom Connectors**, you need OAuth — see [SETUP.md §Adding OAuth for Claude.ai](SETUP.md#adding-oauth-for-claudeai). The OAuth env vars are the same regardless of which host you picked.

---

## What's in the box

```
mcp-gateway-starter/
├── app/
│   ├── main.py        # FastAPI entry point — health check + mounts MCP
│   ├── server.py      # fastmcp server + auth wiring (env-switched)
│   └── tools.py       # The 3 callable tools — replace this to wrap a different data source
├── notes/             # Sample markdown vault — replace with your own
├── tests/             # Smoke tests for the tools
├── .env.example       # All config; copy to .env locally
├── requirements.txt
├── railway.toml       # Railway service config
├── README.md          # This file
├── SETUP.md           # Long-form walkthrough — read this if anything below is unclear
└── PRESENTATION.md    # Slide outline + 3-slide live-demo runbook (for teaching)
```

**The file you'll customize most:** `app/tools.py`. Replace its three functions with whatever your data source needs. The function name becomes the tool name; the docstring becomes the description an AI client sees; the type hints become the JSON Schema. That's the whole API.

---

## Two auth modes

| Mode | When to use | How to enable |
|---|---|---|
| **`bearer`** (default) | Local testing, MCP Inspector, your own scripts, Codex CLI, Cursor | `AUTH_MODE=bearer` + set `MCP_API_KEY` |
| **`oauth`** | Claude.ai Custom Connectors (requires Dynamic Client Registration) | `AUTH_MODE=oauth` + the steps in SETUP.md |

Start with bearer. Switch to OAuth when you're ready to wire it into Claude.ai.

---

## Cost estimate

At low traffic (a few requests per hour):

- **Render** — free tier (sleeps when idle) or $7/month Starter (always on)
- **Railway** — ~$5/month hobby tier (always on, no sleep)
- **Cloud Run** — effectively free under the 2M req/month free tier; pennies above

Scaling notes in [SETUP.md §Costs](SETUP.md#costs).

---

## License & next steps

MIT licensed — fork freely, commercialize, white-label.

Common next moves:

- **Wrap a different data source.** Replace `app/tools.py`. The data source could be Postgres, a CRM API, an Obsidian vault, a Google Drive folder, a CSV catalogue, anything.
- **Add per-principal permissions.** When you start having multiple AI clients calling the same gateway and want them to see different data, add a `.brain/permissions.yml`-style file and check it at each tool call.
- **Add an audit log.** A simple JSONL append at the start of each tool invocation gives you a tail you can review weekly.
- **Multi-tenant.** Run one gateway per tenant on Railway, or one gateway with a `tenant_id` parameter on every tool. The starter ships single-tenant for clarity.

For deeper context on what an MCP gateway is and how to teach this to a group, see [PRESENTATION.md](PRESENTATION.md). For the upgrade path from single-user read-only to team write-with-review (PR-style), see [EVOLVE.md](EVOLVE.md).
