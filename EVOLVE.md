# Evolving the starter

The base starter is **single-user, read-only**. That's deliberate — it's the smallest thing that proves the MCP pattern and stays teachable in one sitting.

This doc sketches the next two evolutions people actually hit:

1. **Team write-with-review** — let staff propose changes; you approve via PR
2. **Per-principal permissions** — different staff see different slices of the brain

Neither is in the code. Both are well-defined upgrades you can make in an afternoon when you're ready.

---

## Evolution 1: Team write-with-review (PR-style)

**The problem.** You've shared the gateway with your team. They want to add and edit notes from inside Claude.ai. You want every change reviewed before it goes live.

**The wrong instinct.** Build a draft/publish workflow into the MCP — status fields, approval queues, a review UI.

**The right instinct.** Git is already a review system. Don't rebuild it.

### Architecture

```
Staff (Claude.ai / Codex / Cursor)
        ↓ propose_note("Q2 client meeting notes", "...content...")
   MCP Gateway
        ↓ git checkout -b proposal/2026-05-21-sarah-q2-client
        ↓ write file → commit → push
        ↓ gh pr create
   GitHub PR opens
        ↓ you review on github.com
        ↓ merge to main
   Webhook → gateway pulls latest
   Live in vault, readable by all staff
```

The vault stops being "files on a Render disk." It becomes a **git working copy of a private GitHub repo**. Read tools `git pull` on a short interval. Write tools never touch `main` directly — they always open a PR.

### What changes

**Vault layer (no code, just setup)**

1. `cd notes && git init && git remote add origin git@github.com:you/agency-brain.git && git push`
2. Generate a fine-grained PAT scoped to that one repo (contents: read+write, PRs: read+write)
3. Add to env:
   ```
   VAULT_REPO=you/agency-brain
   GITHUB_TOKEN=ghp_xxxxx
   ```
4. Enable branch protection on `main`: require 1 review before merge

**`app/tools.py` gains three tools** (the read tools stay as-is):

```python
def propose_note(path: str, content: str, reason: str) -> str:
    """Open a PR proposing a new note. Returns the PR URL."""

def propose_edit(path: str, new_content: str, reason: str) -> str:
    """Open a PR proposing changes to an existing note. Returns the PR URL."""

def list_my_pending_proposals() -> list[dict]:
    """List PRs you've opened that are still awaiting review."""
```

Implementation is roughly:

```python
def propose_note(path: str, content: str, reason: str) -> str:
    principal = current_principal()  # whoever's making the request
    branch = f"proposal/{date.today().isoformat()}-{principal}-{slugify(path)}"

    repo = git.Repo(VAULT_DIR)
    repo.git.checkout("main")
    repo.git.pull()
    repo.git.checkout("-b", branch)

    (VAULT_DIR / path).write_text(content)
    repo.index.add([path])
    repo.index.commit(f"Propose: {path}\n\n{reason}")
    repo.git.push("--set-upstream", "origin", branch)

    pr = github_client.get_repo(VAULT_REPO).create_pull(
        title=f"Propose: {path}",
        body=f"**Proposed by:** {principal}\n**Reason:** {reason}",
        head=branch,
        base="main",
    )
    return pr.html_url
```

Maybe 80 lines once you add error handling, conflict detection, and a helper to find the right branch name when paths collide.

**Per-staff identity** — this is what makes "reviewed as a PR" actually meaningful:

- **Bearer mode:** give each staff member their own key. Map keys to principal names in env:
  ```
  MCP_API_KEY_SARAH=...
  MCP_API_KEY_JAMES=...
  ```
  The gateway resolves the bearer token to a principal name, which becomes the PR author attribution.

- **OAuth mode:** Claude.ai already passes the authenticated user in the JWT. The `principal_id` claim is the author. No extra config.

Either way, every PR carries the proposer's identity. Audit log is free — it's the git history.

**Webhook for "merged → live"** (optional but nice):

```python
@app.post("/webhooks/github")
async def github_webhook(payload: dict):
    if payload.get("action") == "closed" and payload["pull_request"]["merged"]:
        subprocess.run(["git", "pull"], cwd=VAULT_DIR, check=True)
    return {"ok": True}
```

~15 lines. Without it, just `git pull` on a 60-second background task. Even simpler.

### What deliberately stays out

- **No review UI in the gateway.** GitHub has one. Use it.
- **No "draft / publish" status on notes.** Branches and merges already encode that.
- **No "approval permissions" logic.** Branch protection rules on `main` handle it.
- **No notifications.** GitHub already emails you when a PR opens.

### Gotchas

1. **Merge conflicts** when two staff edit the same file in overlapping PRs. Same problem any team has — first to merge wins, second resolves. Markdown is forgiving; YAML frontmatter less so.
2. **The PAT is powerful.** If a bearer token leaks, the attacker can open PRs but can't merge. Annoying, not catastrophic. Rotate annually.
3. **Git-backable data sources only.** Markdown vault: yes. Postgres: use a `proposals` table with `status='pending'` instead. Notion: their API has page versioning — defer to it. CRM: most have native approval workflows.
4. **Don't let the MCP merge its own PRs.** Even for "trusted" staff. The review gate is the whole point.
5. **PR sprawl.** If staff use this 50×/day, you'll drown in PRs. Add a `propose_batch_edit` for related changes, or set a norm: one PR per topic.
6. **The vault directory must be writable** by the gateway process. Render's free tier disk is ephemeral — fine, you re-clone on boot. Railway/Cloud Run persistent volumes work too.

### Cost of this evolution

- 80–120 lines added to `tools.py`
- One new env var pair (`VAULT_REPO`, `GITHUB_TOKEN`)
- One new dependency: `PyGithub` (or shell out to `gh`)
- The base 250-line starter is still readable; you've added one well-scoped capability

---

## Evolution 2: Per-principal permissions

**The problem.** Sarah handles Client A. James handles Client B. They shouldn't see each other's client folders.

**The shape.** Add a `permissions.yml` next to your env, check it at each tool call.

```yaml
# permissions.yml
principals:
  sarah:
    tools: [list_notes, read_note, search_notes, propose_note, propose_edit]
    path_prefix: "clients/acme/"
  james:
    tools: [list_notes, read_note, search_notes, propose_note, propose_edit]
    path_prefix: "clients/widgetco/"
  clark:
    tools: ["*"]
    path_prefix: ""  # full access
```

In each tool:

```python
def list_notes() -> list[str]:
    principal = current_principal()
    prefix = permissions[principal]["path_prefix"]
    return [n for n in all_notes() if n.startswith(prefix)]
```

~30 lines, including loading and caching the permissions file. Reload on file change if you want hot updates.

### Gotchas

1. **Search must filter, not just list.** It's easy to forget that `search_notes` reads content from paths the principal can't see. Filter results by prefix before returning.
2. **Frontmatter leaks.** If notes reference each other (`[[clients/acme/intake]]`), a James-scoped search might surface the existence of Acme. Decide whether that's a leak or not.
3. **Permissions drift.** Add a CI check that `permissions.yml` parses and every referenced tool exists. Easy to typo a tool name and lock someone out.
4. **Don't add roles.** Two staff with the same access? Duplicate the entry. Resist the "users + groups + roles" RBAC instinct until you have 20+ principals.

---

## Evolutions deliberately NOT covered here

These come up but are bigger architectural shifts, not "afternoon upgrades":

- **Multi-tenant SaaS.** Per-tenant isolation, dedicated databases, billing. Different product.
- **Real-time collaboration.** Two people editing the same note simultaneously. Use Obsidian Sync or similar — not the MCP's job.
- **Rich content (images, PDFs, audio).** Markdown handles text. For binary assets, point notes at object storage (S3, R2) and store URLs.
- **Search beyond `grep`.** Once your vault is >1000 notes, naive search gets slow and dumb. Drop in `meilisearch` or `tantivy` as a sidecar; replace `search_notes`' implementation. The tool signature doesn't change.
- **Conversational memory** (the MCP remembers what staff have asked). Different problem — store conversation summaries somewhere, surface via a new `recall(topic)` tool.

Each of these is a real product decision. Don't bolt them onto the starter; build them as their own thing when you actually need them.

---

## When to do which

| Symptom | Evolution |
|---|---|
| "I want to add a note from Claude.ai" | Evolution 1 (write-with-review) |
| "I don't trust the AI to write directly to main" | Evolution 1 |
| "My team is asking for write access" | Evolution 1 + per-principal identity |
| "Staff are seeing each other's client data" | Evolution 2 |
| "The PR queue is too long" | Norm-setting (batch edits), not more code |
| "Search is slow" | Sidecar search engine, not core change |
| "I want this to be a SaaS" | New project, not an evolution |

The starter is load-bearing for *"I have a working MCP gateway."* Everything past that is composition. Add capabilities one at a time, keep each one well-scoped, and resist the SaaS-ification instinct until your usage actually warrants it.
