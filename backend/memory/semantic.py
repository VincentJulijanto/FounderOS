"""
Semantic Memory — stores learned insights about a user over time.
"User performs better with B2B ideas than B2C ideas."
"User has tried service businesses twice, both abandoned."

These insights are extracted from episodic history and used to
improve future recommendations.
"""

import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Integer, select
import anthropic
from ..config import settings


class SemanticBase(DeclarativeBase):
    pass


class SemanticInsight(SemanticBase):
    """A single learned insight about a user."""
    __tablename__ = "semantic_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    insight_type: Mapped[str] = mapped_column(String(64))   # "preference" | "pattern" | "constraint"
    key: Mapped[str] = mapped_column(String(128))            # e.g. "business_model_preference"
    value: Mapped[str] = mapped_column(Text)                  # e.g. "B2B over B2C"
    confidence: Mapped[int] = mapped_column(Integer, default=1)  # increases with repeated evidence
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of supporting sessions
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# SemanticMemory Service
# ─────────────────────────────────────────────

EXTRACTION_PROMPT = """
You are a memory analyst. Given a user's startup journey history, extract semantic insights
— patterns and preferences that should influence future recommendations.

History:
{history}

Extract insights in this JSON format:
{{
  "insights": [
    {{
      "insight_type": "preference|pattern|constraint",
      "key": "short_snake_case_key",
      "value": "clear insight statement",
      "evidence": "what in the history supports this"
    }}
  ]
}}

Only extract insights with clear evidence. Don't speculate.
"""


class SemanticMemory:
    """
    Extracts and stores semantic insights about a user.
    Uses Claude to analyse episodic history and surface patterns.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def extract_and_store(
        self,
        session: AsyncSession,
        user_id: str,
        episodic_history: str,
    ) -> list[SemanticInsight]:
        """
        Extract semantic insights from episodic history and upsert into DB.
        Called after each session ends.
        """
        if not episodic_history or episodic_history == "No previous sessions found.":
            return []

        # Ask Claude to extract patterns
        prompt = EXTRACTION_PROMPT.format(history=episodic_history)
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text

        try:
            data = json.loads(raw.strip().strip("```json").strip("```"))
            insights_data = data.get("insights", [])
        except (json.JSONDecodeError, AttributeError):
            return []

        saved = []
        for item in insights_data:
            # Upsert: if key exists, increase confidence
            result = await session.execute(
                select(SemanticInsight).where(
                    SemanticInsight.user_id == user_id,
                    SemanticInsight.key == item.get("key", ""),
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.value = item.get("value", existing.value)
                existing.confidence += 1
                existing.updated_at = datetime.utcnow()
                saved.append(existing)
            else:
                new_insight = SemanticInsight(
                    user_id=user_id,
                    insight_type=item.get("insight_type", "preference"),
                    key=item.get("key", "unknown"),
                    value=item.get("value", ""),
                    confidence=1,
                    evidence=item.get("evidence", ""),
                )
                session.add(new_insight)
                saved.append(new_insight)

        await session.commit()
        return saved

    async def get_insights(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[SemanticInsight]:
        result = await session.execute(
            select(SemanticInsight)
            .where(SemanticInsight.user_id == user_id)
            .order_by(SemanticInsight.confidence.desc())
        )
        return list(result.scalars().all())

    async def format_for_context(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> str:
        """
        Format semantic memory as context string.
        Example output:
          - [HIGH confidence] Prefers B2B over B2C models
          - [MED confidence] Abandoned service businesses twice — may prefer digital products
        """
        insights = await self.get_insights(session, user_id)
        if not insights:
            return "No semantic insights yet."

        lines = []
        for ins in insights:
            confidence_label = (
                "HIGH" if ins.confidence >= 3
                else "MED" if ins.confidence >= 2
                else "LOW"
            )
            lines.append(f"- [{confidence_label} confidence] {ins.value}")
        return "\n".join(lines)
