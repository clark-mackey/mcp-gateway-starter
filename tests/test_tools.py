"""Smoke tests for the tool functions.

These exercise the tool code directly (not through MCP). For end-to-end MCP
tests, use the MCP Inspector against a running server.

Run: `pytest tests/`
"""
from __future__ import annotations

import os
from pathlib import Path

# Set required env vars BEFORE importing app modules.
os.environ["AUTH_MODE"] = "bearer"
os.environ["MCP_API_KEY"] = "test-key-for-smoke-tests-only"
os.environ["NOTES_DIR"] = str(Path(__file__).parent.parent / "notes")

from app.tools import list_notes, read_note, search_notes  # noqa: E402

# @mcp.tool wraps each function in a FunctionTool object — the original Python
# function lives at .fn. Tests use the .fn attribute to call the underlying
# implementation directly; live MCP clients go through the FunctionTool wrapper.
_list_notes = list_notes.fn
_read_note = read_note.fn
_search_notes = search_notes.fn


def test_list_notes_returns_sample_files():
    notes = _list_notes()
    assert len(notes) >= 3
    assert "welcome.md" in notes
    assert any(n.startswith("concepts") for n in notes)


def test_list_notes_folder_filter():
    notes = _list_notes("concepts")
    assert all(n.startswith("concepts") for n in notes)
    assert len(notes) >= 1


def test_read_note_returns_file_contents():
    text = _read_note("welcome.md")
    assert "MCP gateway" in text


def test_read_note_rejects_traversal():
    import pytest
    with pytest.raises(ValueError, match="escapes the notes vault"):
        _read_note("../../../etc/passwd")


def test_read_note_missing_file():
    import pytest
    with pytest.raises(ValueError, match="No file at"):
        _read_note("does-not-exist.md")


def test_search_notes_finds_hits():
    hits = _search_notes("MCP")
    assert len(hits) > 0
    assert all("path" in h and "line" in h and "text" in h for h in hits)


def test_search_notes_empty_query():
    assert _search_notes("") == []
    assert _search_notes("   ") == []


def test_search_notes_respects_limit():
    hits = _search_notes("the", limit=3)
    assert len(hits) <= 3
