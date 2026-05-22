# Setup walkthrough

Companion to [README.md](README.md). Same steps, with the *why* for each.

## Prerequisites

- Python 3.11+
- `uv` (recommended) or `pip`
- A GitHub account
- An account on a hosting provider — Render (free tier, no card), Railway (~$5/month), or Google Cloud Run (free tier, card required)
- Optional: Node.js + npm if you want the Railway CLI

## Step 1 — Clone and run locally

```bash
gh repo clone clark-mackey/mcp-gateway-starter
cd mcp-gateway-starter

uv venv && source .venv/bin/activate
uv pip install -r requirements.txt

cp .env.example .env
```

Open `.env`. Set `MCP_API_KEY` to a real random string:

```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
-join ((48..57) + (97..102) | Get-Random -Count 64 | % { [char]$_ })
```

Paste the output into `MCP_API_KEY=...` in your `.env`.

Then:

```bash
uvicorn app.main:app --reload --port 8000
```

You should see `Uvicorn running on http://127.0.0.1:8000`.

## Step 2 — Verify it's serving

```bash
curl http://localhost:8000/health
# -> {"status":"ok","auth_mode":"bearer"}
```

If you get a connection error, the server didn't start — re-read uvicorn's output for the real error.

If `/health` works but you get 500s elsewhere, check that `MCP_API_KEY` is set to a real value (the gateway refuses to start with the placeholder).

## Step 3 — Test with MCP Inspector

The [MCP Inspector](https://modelcontextprotocol.io/inspector) is the easiest way to poke an MCP server during development.

1. Open https://modelcontextprotocol.io/inspector
2. Server URL: `http://localhost:8000/mcp/` (note the trailing slash)
3. Auth: select "Bearer Token" — paste your `MCP_API_KEY`
4. Click **Connect**

You should see your three tools (`list_notes`, `read_note`, `search_notes`) listed. Click any to call it.

If the connection fails: check your bearer token matches `MCP_API_KEY` exactly, including no extra whitespace.

## Step 4 — Deploy

Three paths. The gateway code is identical on all of them — only the deploy commands differ. Pick one.

### Path A — Render (recommended)

Render has the gentlest learning curve for non-devs: web UI, GitHub auto-deploy, real free tier, no credit card.

1. Push this repo to your own GitHub account (`gh repo create` or via github.com).
2. Sign up at [render.com](https://render.com) (GitHub login works).
3. **New → Web Service → Connect your repo**.
4. Render auto-detects Python. Confirm these settings:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment**, add:
   - `AUTH_MODE` = `bearer`
   - `MCP_API_KEY` = a fresh random string (`openssl rand -hex 32`)
6. **Create Web Service**. First build takes 3–5 minutes.

When it's live, Render shows the URL (`https://your-gateway.onrender.com`). Verify:

```bash
curl https://your-gateway.onrender.com/health
# -> {"status":"ok","auth_mode":"bearer"}
```

Free-tier note: the service sleeps after ~15 minutes idle and takes ~60s to wake. That breaks Claude.ai connector handshakes on a cold hit. For Claude.ai production use, upgrade to the $7/mo Starter plan (always on).

### Path B — Railway

Install the Railway CLI if you don't have it:

```bash
npm i -g @railway/cli
railway login
```

From the repo root:

```bash
railway init                              # interactive — name your project
railway up                                # builds and deploys
railway variables --set AUTH_MODE=bearer
railway variables --set "MCP_API_KEY=$(openssl rand -hex 32)"  # generate a fresh key for production
railway domain                            # generates a public URL
```

The `railway up` step takes 2–4 minutes the first time (Nixpacks detects Python, installs deps, builds). Subsequent deploys are faster.

After `railway domain` prints your URL, verify:

```bash
curl https://your-gateway.up.railway.app/health
# -> {"status":"ok","auth_mode":"bearer"}
```

If the health check fails, run `railway logs` to see why.

### Path C — Google Cloud Run

Cloud Run scales to zero and gives you 2M requests/month free. Setup is CLI-heavy but a single command once configured.

1. Install the [`gcloud` CLI](https://cloud.google.com/sdk/docs/install) and run `gcloud init` (creates a project, enables billing — billing card required, but you won't be charged at low traffic).
2. Enable Cloud Run: `gcloud services enable run.googleapis.com cloudbuild.googleapis.com`.
3. Deploy from the repo root:

```bash
gcloud run deploy mcp-gateway \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AUTH_MODE=bearer,MCP_API_KEY=$(openssl rand -hex 32)
```

Cloud Build will detect Python, containerize, and push. Takes 3–6 minutes the first time. The CLI prints your URL (`https://mcp-gateway-xxxxx-uc.a.run.app`).

Verify:

```bash
curl https://mcp-gateway-xxxxx-uc.a.run.app/health
# -> {"status":"ok","auth_mode":"bearer"}
```

Cold starts on Cloud Run are ~2–3s (much faster than Render free tier), and scale-to-zero means you pay nothing when idle.

## Step 5 — Connect from your AI client

### Codex CLI

Codex has built-in MCP support. Edit your Codex config:

```toml
[mcp.servers.my-vault]
url = "https://your-gateway.up.railway.app/mcp/"
headers = { Authorization = "Bearer <your MCP_API_KEY>" }
```

Restart Codex. The three tools should appear in any new session.

### Claude Code

Edit `~/.claude/settings.json` to register the MCP server:

```json
{
  "mcpServers": {
    "my-vault": {
      "url": "https://your-gateway.up.railway.app/mcp/",
      "headers": {
        "Authorization": "Bearer <your MCP_API_KEY>"
      }
    }
  }
}
```

Restart Claude Code. The tools appear in the next session.

### Cursor

Cursor's MCP support is added in Settings → Features → Model Context Protocol. Same URL + bearer pattern.

### Claude.ai (Custom Connectors)

Claude.ai requires OAuth — bearer mode won't work. Continue to "Adding OAuth for Claude.ai" below.

---

## Adding OAuth for Claude.ai

Claude.ai Custom Connectors use OAuth 2.0 with Dynamic Client Registration (DCR). The gateway already has the machinery; you just switch modes and provide two more env vars.

> The commands below show Railway syntax. The env vars themselves (`AUTH_MODE`, `OAUTH_ISSUER_URL`, `OAUTH_JWT_SECRET`) are identical on every host — set them through Render's Environment tab, the `gcloud run services update --set-env-vars` flag, or whichever host you picked.

### Step A — Generate a JWT secret

```bash
openssl rand -hex 32
```

Save the output. This is `OAUTH_JWT_SECRET`.

### Step B — Set the OAuth env vars

```bash
railway variables --set AUTH_MODE=oauth
railway variables --set OAUTH_ISSUER_URL=https://your-gateway.up.railway.app
railway variables --set OAUTH_JWT_SECRET=<the output from step A>
```

Replace `your-gateway.up.railway.app` with your actual Railway domain.

### Step C — Re-deploy and verify

```bash
railway up
curl https://your-gateway.up.railway.app/health
# -> {"status":"ok","auth_mode":"oauth"}
```

You can also verify the OAuth discovery endpoint:

```bash
curl https://your-gateway.up.railway.app/.well-known/oauth-authorization-server
# -> JSON describing the OAuth endpoints (issuer, /register, /authorize, /token)
```

### Step D — Add the connector in Claude.ai

1. Open [claude.ai](https://claude.ai) → your profile → **Settings** → **Custom Connectors** → **Add**.
2. Paste your gateway URL: `https://your-gateway.up.railway.app/mcp/`.
3. Claude.ai will hit your `/.well-known` endpoint, register itself via DCR, then prompt you to authorize.
4. After authorization, you should see your three tools listed.

In any new Claude.ai conversation, the tools are now available. Try: *"list my notes."*

### Troubleshooting OAuth

- **"Connector failed to register"** — check that `OAUTH_ISSUER_URL` exactly matches your Railway domain (including `https://`, no trailing slash). Re-deploy after fixing.
- **"Invalid JWT"** — `OAUTH_JWT_SECRET` may have changed between when Claude.ai issued the token and when the gateway tried to verify it. Re-authorize the connector in Claude.ai's UI.
- **No `.well-known` endpoint** — confirm `AUTH_MODE=oauth` is set in Railway and the latest deploy is live (`railway logs --tail`).

---

## Costs

Low-traffic single-user gateway (a few requests per hour, ~150 MB memory, ~0.05 vCPU avg):

| Host | Cost | Notes |
|---|---|---|
| **Render free** | $0 | Sleeps after ~15 min idle; cold start ~60s. Fine for testing, breaks Claude.ai connectors. |
| **Render Starter** | $7/month | Always on. Good production default if you don't already use Railway. |
| **Railway hobby** | ~$5/month | Always on. $5/mo minimum includes ~500 compute hours, plenty for this. |
| **Cloud Run** | $0–1/month | Free under 2M req/mo. Card required even if you stay free. |

If you scale to a paid product with hundreds of users, the starter's single-tenant architecture is the wrong shape regardless of host — you'd want per-tenant isolation, a real database, etc.

---

## Going further

This is a starter — load-bearing for "I have a working gateway" but it's the floor, not the ceiling. Common next moves:

### Wrap a different data source

Replace `app/tools.py` with functions that talk to your real backend. Examples:

- **Postgres**: `import psycopg`; tools become `query_clients`, `get_client_detail`, etc.
- **CRM (HubSpot / Salesforce)**: tools wrap their REST API
- **Notion**: tools wrap the Notion API
- **CSV catalogues**: tools read and search across CSVs

The MCP surface area (the three function signatures) is the only thing the AI client sees. The implementation can be anything.

### Add per-principal permissions

Today every authenticated request can call every tool. If you want to scope access (e.g., one client can only read its own notes), add a permissions file:

```yaml
# permissions.yml
principals:
  claude-ai-acme-corp:
    tools: [list_notes, read_note]
    folder_filter: "clients/acme/"
  claude-ai-other-client:
    tools: [list_notes, read_note]
    folder_filter: "clients/other/"
```

Then at the top of each tool function, read the principal from the auth context and filter accordingly. fastmcp surfaces the authenticated principal via `mcp.context.principal_id` (or similar — check the version's API).

### Add an audit log

A simple append-only log of every tool call:

```python
import json, datetime
def audit(principal: str, tool: str, args: dict, result_summary: str):
    with open("audit.jsonl", "a") as f:
        f.write(json.dumps({
            "ts": datetime.datetime.utcnow().isoformat(),
            "principal": principal,
            "tool": tool,
            "args": args,
            "result": result_summary,
        }) + "\n")
```

Call from each tool. Review weekly. For real production, ship logs to a real logging service (Datadog, Logflare, your own ELK).

### Multi-tenant

Two patterns:

1. **One gateway per tenant.** Deploy a separate Railway service per client. Simple isolation, higher cost (one $5/mo bill per client).
2. **One gateway, tenant_id parameter.** Add `tenant_id: str` to every tool; permissions.yml routes tenant → data namespace. Cheaper but tenancy logic is in your code.

For more than ~5 tenants, option 2 wins on cost. For regulated tenants (HIPAA, etc.), option 1 wins on isolation argument.

---

## What's NOT in this starter

These are deliberate omissions for teaching clarity:

- **Rate limiting.** Add `slowapi` if you need it.
- **Caching.** Add `cachetools` or Redis if your tool calls are expensive.
- **Async I/O for the tools.** Tools are sync because reading markdown files is sync. If your backend is async (a database, an API), make tools async with `async def`.
- **Metrics / observability.** Wire OpenTelemetry or Sentry if you're running in production.
- **Per-tool rate limits.** Add per-tool decorators if you need it.

Each of these is a one-paragraph addition to a teachable starter. Add as your real workload demands. Don't add speculatively.
