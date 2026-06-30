"""
In-process Memory Store — the Phase 5 Memory Loop, hackathon backing.

The Postgres-backed `EpisodicMemory` / `SemanticMemory` modules in this package
describe the *production* schema. For the keyless hackathon build (no Postgres,
mock LLM), this module provides an equivalent in-process implementation that
makes the memory loop actually *run and learn* end-to-end:

    analyze  → load context (episodic + semantic) → feed Venture Partner
             → record episode
    feedback → update outcome → re-derive semantic insights (heuristic, no LLM)

Insight extraction here is deliberately rule-based (deterministic, key-free) so
the loop demonstrably influences recommendations without a live model. When a
real key is available, `SemanticMemory.extract_and_store` (Qwen) can replace the
heuristic without changing any caller — both emit the same `[LABEL] value` lines.

State is per-process and resets on restart — fine for a demo, swap for the
Postgres services in production.
"""

from __future__ import annotations

import threading
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ─────────────────────────────────────────────
# Records
# ─────────────────────────────────────────────

@dataclass
class Episode:
    """One FounderOS session for a user (episodic memory)."""
    recommendation_id: str
    recommended_idea: str
    startup_score: float
    top_idea_names: List[str] = field(default_factory=list)
    outcome: Optional[str] = None          # launched | abandoned | in_progress
    feedback: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Insight:
    """A learned pattern about a user (semantic memory)."""
    insight_type: str   # preference | pattern | constraint
    key: str
    value: str
    confidence: int     # higher = more supporting evidence


_OUTCOMES = {"launched", "abandoned", "in_progress"}


# ─────────────────────────────────────────────
# Store
# ─────────────────────────────────────────────

class MemoryStore:
    """Thread-safe, in-process episodic + semantic memory for the agent society."""

    def __init__(self) -> None:
        self._episodes: Dict[str, List[Episode]] = {}
        self._insights: Dict[str, List[Insight]] = {}
        self._by_rec_id: Dict[str, Episode] = {}
        self._lock = threading.Lock()

    # ── Episodic ──────────────────────────────────────────────────────────

    def record_session(
        self,
        user_id: str,
        recommendation_id: str,
        recommended_idea: str,
        startup_score: float,
        top_idea_names: Optional[List[str]] = None,
    ) -> Episode:
        """Persist a completed analysis as an episodic entry."""
        episode = Episode(
            recommendation_id=recommendation_id,
            recommended_idea=recommended_idea,
            startup_score=startup_score,
            top_idea_names=list(top_idea_names or []),
        )
        with self._lock:
            self._episodes.setdefault(user_id, []).append(episode)
            self._by_rec_id[recommendation_id] = episode
        return episode

    def update_outcome(
        self,
        user_id: str,
        recommendation_id: str,
        outcome: Optional[str],
        feedback: Optional[str] = None,
    ) -> bool:
        """
        Record what actually happened with a past recommendation, then re-derive
        semantic insights for the user. Returns False if the episode is unknown.
        """
        with self._lock:
            episode = self._by_rec_id.get(recommendation_id)
            if episode is None:
                return False
            if outcome is not None:
                episode.outcome = outcome
            if feedback is not None:
                episode.feedback = feedback
            episode.updated_at = datetime.utcnow()
        # Learning step — runs outside the lock; extract takes its own snapshot.
        self._extract_insights(user_id)
        return True

    def get_history(self, user_id: str, limit: int = 5) -> List[Episode]:
        with self._lock:
            episodes = list(self._episodes.get(user_id, []))
        return episodes[-limit:][::-1]  # most recent first

    def format_episodic(self, user_id: str) -> str:
        """Human-readable episodic block for the VP prompt."""
        episodes = self.get_history(user_id)
        if not episodes:
            return "No previous sessions found."
        lines = []
        for e in episodes:
            outcome_str = e.outcome or "no feedback yet"
            lines.append(
                f"- {e.created_at.strftime('%b %Y')}: "
                f"Recommended '{e.recommended_idea}' (score {e.startup_score}). "
                f"Outcome: {outcome_str}."
            )
        return "\n".join(lines)

    # ── Semantic ──────────────────────────────────────────────────────────

    def get_insights(self, user_id: str) -> List[Insight]:
        with self._lock:
            return list(self._insights.get(user_id, []))

    def format_semantic(self, user_id: str) -> str:
        """Human-readable semantic block for the VP prompt."""
        insights = self.get_insights(user_id)
        if not insights:
            return "No semantic insights yet."
        lines = []
        for ins in insights:
            label = (
                "HIGH" if ins.confidence >= 3
                else "MED" if ins.confidence >= 2
                else "LOW"
            )
            lines.append(f"- [{label} confidence] {ins.value}")
        return "\n".join(lines)

    def _extract_insights(self, user_id: str) -> List[Insight]:
        """
        Re-derive semantic insights from the user's full episodic history.
        Deterministic rule-based extraction — no LLM, so it runs keyless.
        Confidence scales with how much evidence supports each pattern.
        """
        with self._lock:
            episodes = list(self._episodes.get(user_id, []))

        insights: List[Insight] = []
        outcomes = Counter(e.outcome for e in episodes if e.outcome)

        abandoned = outcomes.get("abandoned", 0)
        launched = outcomes.get("launched", 0)

        if abandoned >= 2:
            insights.append(Insight(
                insight_type="constraint",
                key="abandonment_pattern",
                value=(
                    f"Has abandoned {abandoned} past ventures — favour ideas with a "
                    "faster time-to-value and lower upfront commitment."
                ),
                confidence=min(abandoned, 3),
            ))
        if launched >= 2:
            insights.append(Insight(
                insight_type="pattern",
                key="execution_track_record",
                value=(
                    f"Has launched {launched} past ventures — can be trusted with "
                    "more ambitious scope and a longer build."
                ),
                confidence=min(launched, 3),
            ))

        scored = [e.startup_score for e in episodes if e.startup_score is not None]
        if len(scored) >= 2:
            avg = round(sum(scored) / len(scored), 1)
            insights.append(Insight(
                insight_type="preference",
                key="historical_score_baseline",
                value=(
                    f"Past recommendations averaged {avg}/10 — aim to clear that bar "
                    "or explain why a lower-scoring idea fits better this time."
                ),
                confidence=2 if len(scored) >= 3 else 1,
            ))

        # Recurring idea themes across the user's recommended ideas.
        theme = self._dominant_theme(episodes)
        if theme:
            word, count = theme
            insights.append(Insight(
                insight_type="preference",
                key="recurring_theme",
                value=(
                    f"Gravitates toward '{word}' ideas (seen in {count} sessions) — "
                    "weigh whether to lean in or deliberately diversify."
                ),
                confidence=min(count, 3),
            ))

        with self._lock:
            self._insights[user_id] = insights
        return insights

    @staticmethod
    def _dominant_theme(episodes: List[Episode]) -> Optional[tuple[str, int]]:
        """Most common meaningful word across recommended idea names (>=2 sessions)."""
        stop = {
            "the", "a", "an", "for", "and", "of", "to", "ai", "app", "platform",
            "your", "with", "by", "studio", "hub", "pro",
        }
        words: Counter = Counter()
        for e in episodes:
            for raw in e.recommended_idea.lower().replace("-", " ").split():
                w = raw.strip(".,!?:;()")
                if len(w) > 2 and w not in stop:
                    words[w] += 1
        if not words:
            return None
        word, count = words.most_common(1)[0]
        return (word, count) if count >= 2 else None

    # ── Combined context for the agent society ────────────────────────────

    def build_context(self, user_id: str) -> str:
        """
        The memory_context string threaded into the graph and consumed by the
        Venture Partner. Empty-ish for first-time users (the VP treats it as
        'no prior history').
        """
        episodic = self.format_episodic(user_id)
        semantic = self.format_semantic(user_id)
        if episodic == "No previous sessions found." and semantic == "No semantic insights yet.":
            return ""
        return (
            "PAST SESSIONS (episodic):\n"
            f"{episodic}\n\n"
            "LEARNED INSIGHTS (semantic):\n"
            f"{semantic}"
        )

    def summary(self, user_id: str) -> dict:
        """Structured view for GET /api/memory/{user_id}."""
        episodes = self.get_history(user_id, limit=50)
        return {
            "user_id": user_id,
            "session_count": len(episodes),
            "history": [
                {
                    "recommendation_id": e.recommendation_id,
                    "idea": e.recommended_idea,
                    "score": e.startup_score,
                    "outcome": e.outcome or "pending",
                }
                for e in episodes
            ],
            "semantic_insights": [
                {
                    "type": ins.insight_type,
                    "key": ins.key,
                    "value": ins.value,
                    "confidence": ins.confidence,
                }
                for ins in self.get_insights(user_id)
            ],
        }

    def reset(self) -> None:
        """Clear all memory — used by tests for isolation."""
        with self._lock:
            self._episodes.clear()
            self._insights.clear()
            self._by_rec_id.clear()


# Process-wide singleton — imported by main.py.
memory_store = MemoryStore()
