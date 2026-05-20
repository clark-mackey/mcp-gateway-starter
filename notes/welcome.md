# Welcome to your MCP gateway

If you're reading this through an AI client (Claude, Codex, Cursor) — that means the gateway is working. You're talking to a small FastAPI service that read this markdown file off disk and handed it to your AI.

## What this folder is

Sample data for the starter. Replace these notes with your own — your meeting notes, your client research, your product docs, your internal wiki.

## How an AI client uses this

The gateway exposes three tools to your AI client:

- `list_notes()` — see what's in the vault
- `read_note(path)` — read one note in full
- `search_notes(query)` — substring search across all notes

When you say "summarize my notes on X" or "what did we decide about Y," the AI calls these tools to find the relevant material and bring it into context.

## Customize this

Add your own markdown files in this folder. Sub-folders work too. The tools auto-discover everything ending in `.md`.

For non-markdown data sources (Postgres, CRM, APIs), replace `app/tools.py` — that's the only file you need to change.
