"""
Memory package.

`memory_store` (in-process, no dependencies) is the active Phase 5 backing and is
always importable. `EpisodicMemory` / `SemanticMemory` are the Postgres-backed
*production* services — they require sqlalchemy + asyncpg, so they are imported
lazily to keep the keyless/mock build working without those packages installed.
"""

from .store import MemoryStore, Episode, Insight, memory_store

__all__ = [
    "MemoryStore",
    "Episode",
    "Insight",
    "memory_store",
    "EpisodicMemory",
    "SemanticMemory",
]


def __getattr__(name: str):
    # Lazy — only pulls in sqlalchemy/asyncpg when the Postgres services are
    # actually requested (e.g. production wiring), never at import time.
    if name == "EpisodicMemory":
        from .episodic import EpisodicMemory
        return EpisodicMemory
    if name == "SemanticMemory":
        from .semantic import SemanticMemory
        return SemanticMemory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
