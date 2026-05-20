# Example: what a tool call looks like end-to-end

When you say to your AI client "summarize the auth options in my MCP gateway notes," here's what happens:

1. **Client decides to call a tool.** The AI reads the docstrings of the available tools and chooses `search_notes` with query="auth options".
2. **Wire request.** The client sends an MCP `tools/call` message over HTTP to `https://your-gateway/mcp/`, with auth header and the tool name + arguments.
3. **fastmcp dispatches.** The library validates the bearer/JWT, parses the arguments against the tool's JSON Schema, calls your Python function.
4. **Your function runs.** `search_notes("auth options")` scans the vault and returns a list of hits.
5. **Response back.** fastmcp serializes the return value as JSON and sends it back to the client.
6. **AI continues.** With the search results in context, the AI can call `read_note(path)` on any promising hit to get the full text.
7. **Synthesis.** The AI reads the relevant content and writes the summary you asked for.

The whole round trip is usually under 500ms per tool call. The slowest step is your function's actual work — for this template that's a linear file scan, but in production it might be a database query or an API call.

## Why this is powerful

The AI client doesn't need to know anything about your data — it just sees three tools. You can change the implementation (move from markdown to Postgres, add caching, add per-user filtering) without changing how the AI uses it.
