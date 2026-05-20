"""Tools — the surface area your AI client sees.

Each function decorated with `@mcp.tool` becomes a callable tool. The function's
docstring becomes its description (the LLM reads it to decide when to call).
Type hints become the JSON Schema the AI client uses for parameter validation.

**To wrap a different data source: replace this entire file.** That's the whole
adaptation point of this template. Postgres, your CRM API, a CSV catalogue,
Notion — anything you can express as Python functions with type hints.
"""
from __future__ import annotations

from pathlib import Path

from app.server import mcp, NOTES_DIR


def _safe_resolve(path: str) -> Path:
    """Resolve `path` inside NOTES_DIR; reject paths that escape the vault.

    Why: if you let an AI client pass arbitrary paths, a request like
    `../../../etc/passwd` could read files outside the vault. This is the same
    "directory traversal" class of bug that affects any tool exposing file
    I/O. Always validate.
    """
    full = (NOTES_DIR / path).resolve()
    notes_dir = NOTES_DIR.resolve()
    if not (full == notes_dir or notes_dir in full.parents):
        raise ValueError(f"Path {path!r} escapes the notes vault.")
    return full


@mcp.tool
def list_notes(folder: str = "") -> list[str]:
    """List all markdown notes in the vault, optionally filtered to a sub-folder.

    Returns a sorted list of paths relative to the vault root.
    Examples: list_notes() -> all notes; list_notes("concepts") -> just that folder.
    """
    base = _safe_resolve(folder) if folder else NOTES_DIR
    if not base.is_dir():
        return []
    return sorted(str(p.relative_to(NOTES_DIR)) for p in base.rglob("*.md"))


@mcp.tool
def read_note(path: str) -> str:
    """Read the full text of a note by its vault-relative path.

    Example: read_note("concepts/mcp-overview.md") -> the file's contents.
    Raises ValueError if the path escapes the vault or doesn't exist.
    """
    full = _safe_resolve(path)
    if not full.is_file():
        raise ValueError(f"No file at {path!r}.")
    return full.read_text(encoding="utf-8")


@mcp.tool
def search_notes(query: str, limit: int = 10) -> list[dict]:
    """Search all notes for substring matches. Returns up to `limit` hits.

    Each hit: {"path": str, "line": int, "text": str}. Case-insensitive.

    For production: replace with a real search engine (Tantivy, Meilisearch,
    Postgres FTS). This linear scan is fine for vaults under ~500 notes.
    """
    if not query.strip():
        return []
    needle = query.lower()
    hits: list[dict] = []
    for note in NOTES_DIR.rglob("*.md"):
        try:
            text = note.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if needle in line.lower():
                hits.append(
                    {
                        "path": str(note.relative_to(NOTES_DIR)),
                        "line": line_no,
                        "text": line.strip(),
                    }
                )
                if len(hits) >= limit:
                    return hits
    return hits
