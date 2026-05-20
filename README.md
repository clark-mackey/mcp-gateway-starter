# mcp-gateway-starter

A minimal, teachable starter for an **MCP gateway** — a service that lets AI clients (Claude.ai, Codex, Cursor) call your tools and read your knowledge.

This template wraps a folder of markdown notes and exposes three tools: `list_notes`, `read_note`, `search_notes`. You can swap the markdown layer for any data source (Postgres, Notion, your CRM, your CSV files) by replacing **one file** — `app/tools.py`.

**~250 lines of Python. Deploys to Railway in 10 minutes. Two auth modes — bearer for local dev, OAuth for Claude.ai Custom Connectors.**

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

## Deploy to Railway (10 minutes)

```bash
# 1. Install Railway CLI (one time)
npm i -g @railway/cli && railway login

# 2. From this repo
railway init                    # creates a Railway project
railway up                      # deploys

# 3. Set env vars
railway variables set AUTH_MODE=bearer
railway variables set MCP_API_KEY="$(openssl rand -hex 32)"

# 4. Generate a public URL
railway domain                  # prints e.g. https://your-gateway.up.railway.app

# 5. Test
curl https://your-gateway.up.railway.app/health
#    -> {"status":"ok","auth_mode":"bearer"}
```

You're now live. Your MCP endpoint is `https://your-gateway.up.railway.app/mcp/`. Point any MCP client at it; pass `Authorization: Bearer <your-MCP_API_KEY>`.

For **Claude.ai Custom Connectors**, you need OAuth — see [SETUP.md §Adding OAuth for Claude.ai](SETUP.md#adding-oauth-for-claudeai).

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

Railway hobby tier (~$5/month + ~$0.000463/GB-hour compute) runs this gateway comfortably under $5/month at low traffic. Scaling notes in SETUP.md §Costs.

---

## License & next steps

MIT licensed — fork freely, commercialize, white-label.

Common next moves:

- **Wrap a different data source.** Replace `app/tools.py`. The data source could be Postgres, a CRM API, an Obsidian vault, a Google Drive folder, a CSV catalogue, anything.
- **Add per-principal permissions.** When you start having multiple AI clients calling the same gateway and want them to see different data, add a `.brain/permissions.yml`-style file and check it at each tool call.
- **Add an audit log.** A simple JSONL append at the start of each tool invocation gives you a tail you can review weekly.
- **Multi-tenant.** Run one gateway per tenant on Railway, or one gateway with a `tenant_id` parameter on every tool. The starter ships single-tenant for clarity.

For deeper context on what an MCP gateway is and how to teach this to a group, see [PRESENTATION.md](PRESENTATION.md).
