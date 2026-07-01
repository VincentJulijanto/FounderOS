"""
FounderOS — per-company Obsidian markdown vault (Decision #1: vault only).

This is the single durable memory for the board. Each company has a folder under
VAULT_PATH holding markdown decision notes with YAML frontmatter. Retrieval is
LLM-driven note selection over a small index (frontmatter + filename + one-line
summary) — no embeddings, no vector DB (Decision #2).

Contract signatures (frozen in docs/architecture.md):
    read(company_id, query) -> ContextBundle
    write_back(company_id, decision, recommendation, learnings) -> None

The vault is mock-safe: with no notes it returns an empty ContextBundle, so the
board simply runs as a first session. VAULT_PATH is env-configurable, never
hardcoded (Decision #8).
"""

from .store import Vault, read, write_back, record_outcome, history

__all__ = ["Vault", "read", "write_back", "record_outcome", "history"]
