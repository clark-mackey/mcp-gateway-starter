# Presentation materials

Companion notes for teaching this template to a group. Friday 2026-05-22 reference; reusable for future sessions.

---

## Slide outline (15 slides, ~45–50 min total)

| # | Title | Time | Notes |
|---|---|---|---|
| 1 | Title — MCP Gateways: Give Your AI Tools | 1 min | "Show of hands — who's used Claude.ai? Codex? Cursor? Built anything that integrates with them?" |
| 2 | The problem — N×M integrations | 2 min | Picture: many AI clients × many tools = chaos. Per-client integration per tool. |
| 3 | The solution — MCP | 2 min | One protocol. Every AI client speaks it. Every tool implements it once. N+M, not N×M. |
| 4 | What an MCP gateway actually IS | 3 min | A small HTTP service. Exposes "tools" (callable functions) and "resources" (readable content). Speaks MCP over HTTP. |
| 5 | The architecture | 3 min | Diagram: AI client → MCP gateway → your data. Auth between client and gateway. |
| 6 | **LIVE DEMO — slide 1: "What you'll see in the next 15 minutes"** | 1 min | Clone repo → deploy to Railway → connect from Claude.ai → ask it about your notes. (Slide is the deliverable preview.) |
| 7 | **LIVE DEMO — slide 2: "The starter template"** | 1 min | One file you customize: `app/tools.py`. Three functions. That's the API. (Slide stays up while you switch to the terminal.) |
| 8 | **LIVE DEMO — slide 3: "What it looks like running"** | 1 min | Final-state screenshot of Claude.ai calling a tool against your live gateway. (Up at the end of the demo, while you summarize what happened.) |
| 9 | The auth question | 4 min | Bearer for dev/Codex/Cursor. OAuth+DCR for Claude.ai. Both shipped in the template. |
| 10 | The cost | 2 min | Railway hobby = $5/mo. Your gateway runs at ~$5–7/mo for low-traffic single-tenant. |
| 11 | Productizing — wrap your own data | 4 min | Postgres example. CRM example. Notion example. The 3-function surface stays the same; the implementation changes. |
| 12 | Productizing — multi-tenant | 3 min | Two patterns: one gateway per tenant (simple, $5/mo each) vs. one gateway with tenant_id (cheaper, more logic). When each wins. |
| 13 | What's next once you have a gateway | 4 min | Per-principal permissions, audit logs, observability. None of this is in the starter — add as your workload demands. |
| 14 | Resources + the repo URL | 1 min | github.com/clark-mackey/mcp-gateway-starter — clone it, fork it, ship something on top of it. |
| 15 | Q&A | 10 min | Likely questions in §"Anticipated Q&A" below. |

**Live-demo block is slides 6 / 7 / 8 — three slides, ~15 minutes of terminal/browser time between them.**

---

## Live demo runbook (15 minutes of actual building)

This is the script for what happens WHILE slides 6–7–8 are on screen. Practice once before Friday.

### Pre-flight (do BEFORE the talk)

- [ ] One **reference gateway** already deployed on Railway, URL bookmarked. This is your "I made one earlier" backup if anything breaks live.
- [ ] Reference gateway's Claude.ai Custom Connector already added and authorized in your Claude.ai account. If the live demo's Claude.ai connector fails to register, switch tabs to a Claude.ai conversation that already has the reference gateway connected.
- [ ] Repo cloned on your demo machine. Run `uvicorn app.main:app` once before the talk to warm the dependency cache.
- [ ] Railway CLI logged in (`railway whoami` returns your user).
- [ ] Browser tabs prepped:
  - GitHub repo page (for the "clone this" slide)
  - Railway dashboard (so the build progress is visible)
  - Claude.ai with Custom Connectors page open
  - The reference gateway's Claude.ai conversation as the backup
- [ ] Terminal pre-positioned in `~/Code/` ready to clone, fonts large enough for the back row.

### The 15-minute live build

**Minute 0–2 — Clone**

Slide 6 stays up. You narrate while running:

```bash
gh repo clone clark-mackey/mcp-gateway-starter demo-gateway
cd demo-gateway
ls
```

Talk through what's in the box. Open `app/tools.py` in the editor on a side panel — point at the three decorated functions. "This is the whole API. Everything else is plumbing."

**Minute 2–5 — Deploy to Railway**

Switch to slide 7. Run:

```bash
railway init
# pick a project name when prompted
railway up
```

While the build runs (~2–3 min), narrate: "Railway is detecting Python, installing FastAPI + fastmcp, building the container. We could do this with Render, Fly.io, Vercel — Railway is just my preference for FastAPI."

When the build finishes:

```bash
railway variables --set AUTH_MODE=oauth
railway variables --set OAUTH_ISSUER_URL=https://<the domain Railway just created>
railway variables --set OAUTH_JWT_SECRET=<paste a pre-generated secret>
railway up   # re-deploy with the new env vars
railway domain
```

Show the live `/health` endpoint:

```bash
curl https://<your-domain>/health
```

"There's the gateway. Now let's connect Claude.ai."

**Minute 5–10 — Connect Claude.ai**

Switch to Claude.ai → Custom Connectors → Add.

Paste the gateway URL. Claude.ai hits `/.well-known/oauth-authorization-server`, registers itself, prompts for authorization. Click through.

This is the most likely thing to fail live. **If it fails:** stay calm, say "this is why we have a backup" — switch tabs to the reference gateway you set up before the talk. Continue with the reference instance.

**Minute 10–15 — Use it**

Switch to a Claude.ai conversation. Ask:

> "List the notes in my gateway."

Claude calls `list_notes()`. You see the tool-call indicator. Result returns. Claude says: "Here are your notes: welcome.md, concepts/mcp-overview.md, concepts/auth-modes.md, examples/sample-tool-call.md."

Then:

> "What does the welcome note say?"

Claude calls `read_note("welcome.md")`. Result returns. Claude summarizes.

Then:

> "Search my notes for 'OAuth'."

Claude calls `search_notes("OAuth")`. Hits return. Claude lists them.

Switch to slide 8 — the "what it looks like running" screenshot — and summarize: "From `gh repo clone` to Claude calling tools against my live gateway: about 12 minutes. The code that made this possible: ~250 lines of Python, half of which is comments."

---

## Anticipated Q&A

**"What about latency?"**
Tool calls usually round-trip in under 500ms. Bottleneck is your tool's actual work, not the MCP layer.

**"What about cost at scale?"**
$5/month covers low-traffic single-tenant. For paid SaaS scale (hundreds of users, frequent calls), you'd outgrow Railway hobby; budget $20–50/month per dedicated gateway service, or shard tenants by Postgres schema.

**"What about security — the AI calls my Postgres? Isn't that scary?"**
The AI never calls Postgres directly. It calls *your tool functions*, which YOU wrote, with whatever guards YOU put in. The AI is talking to a Python function you control, not your database.

**"What if my data is sensitive (HIPAA, PII)?"**
Use a private MCP gateway (don't expose your tools publicly), authenticate every call (bearer or OAuth), audit every call, and apply per-principal permissions. Don't put raw PHI in tool return values; redact at the tool layer. The architecture is fine; the disciplines around it are what make it compliant.

**"Can I sell access to my gateway as a product?"**
Yes. The OAuth + DCR pattern means each customer registers their own client_id. You can revoke per-customer. Pricing is your call.

**"Does this work with custom GPTs / GPT Actions?"**
GPT Actions use OpenAPI, not MCP. Different protocol. But the same Python backend can expose both — `app/main.py` could serve `/mcp/` for MCP clients and `/openapi/` for GPT Actions.

**"What's the difference between MCP and function calling?"**
Function calling is the AI-vendor-specific mechanism for letting an LLM invoke tools (OpenAI has it, Anthropic has it, etc.). MCP is the transport protocol that carries those tool calls across HTTP between a client and an external server. They're not alternatives; they compose.

**"Why fastmcp and not Anthropic's own MCP SDK?"**
fastmcp is the most production-mature Python implementation. Anthropic ships an MCP SDK too; fastmcp tends to be ahead on features and has stronger FastAPI integration. As of 2026 either works.

**"What about logs/observability?"**
The starter is intentionally lean. For production: wire structured logging (use `loguru` or stdlib `logging`), ship logs to Logflare/Better Stack/Datadog, add OpenTelemetry traces, add Sentry for error capture. None of it is in the starter; all of it is well-trodden territory.

**"Can I run this without Railway?"**
Yes. Render, Fly.io, Vercel, your own VPS, your own Kubernetes cluster — anywhere Python runs. Railway is my preference because of $5/mo simplicity + fast deploy iteration.

---

## After the talk

- Push any improvements to the starter back to the repo.
- Open issues against your own pain points so the next presenter has them resolved.
- Track who from the audience cloned/forked the repo (GitHub Insights → Traffic). Follow up at 1 week and 1 month — what did they build, what got stuck?
