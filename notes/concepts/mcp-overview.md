# What is MCP

MCP — Model Context Protocol — is a standardized way for AI clients to talk to external tools and data sources. Think of it as the USB-C of AI integrations: one protocol, many implementations.

## The two sides

- **MCP servers** expose tools (callable functions) and resources (readable content) over a standard protocol.
- **MCP clients** are the AI applications: Claude.ai, Codex CLI, Cursor, Claude Code, custom agents.

A client can connect to many servers simultaneously. A server can serve many clients.

## What this gateway is

This repo is an **MCP server**. It speaks the MCP protocol over HTTP. The protocol implementation is handled by the `fastmcp` Python library — your code just defines tool functions; fastmcp handles the wire format.

## Why a gateway, not a per-client integration

Without MCP: every AI client needs a custom integration with every tool. N×M problem.
With MCP: every tool implements MCP once. Every AI client speaks MCP. N+M problem.

Standard protocols beat bespoke integrations.
