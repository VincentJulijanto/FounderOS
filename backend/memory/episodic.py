"""
Episodic Memory — stores what happened in each session.
"User previously attempted a tutoring business."

Uses PostgreSQL (via SQLAlchemy async) for persistence.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Text, select
from ..config import settings


# ─────────────────────────────────────────────
# DB Setup
# ─────────────────────────────────────────────

engine = create_async_engine(settings.database_url, echo=False)


class Base(DeclarativeBase):
    pass


class EpisodicEntry(Base):
    """One entry per FounderOS session."""
    __tablename__ = "episodic_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    session_id: Mapped[str] = mapped_column(String(64))
    recommendation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # What was recommended
    recommended_idea: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    startup_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    top_ideas_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list

    # What happened
    outcome: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)   # launched | abandoned | in_progress
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────
# EpisodicMemory Service
# ─────────────────────────────────────────────

class EpisodicMemory:
    """
    Store and retrieve episodic (session-level) memories for a user.
    """

    async def save(
        self,
        session: AsyncSession,
        user_id: str,
        session_id: str,
        recommendation_id: str,
        recommended_idea: str,
        startup_score: float,
        top_ideas_json: str,
    ) -> None:
        entry = EpisodicEntry(
            user_id=user_id,
            session_id=session_id,
            recommendation_id=recommendation_id,
            recommended_idea=recommended_idea,
            startup_score=startup_score,
            top_ideas_json=top_ideas_json,
        )
        session.add(entry)
        await session.commit()

    async def update_outcome(
        self,
        session: AsyncSession,
        recommendation_id: str,
        outcome: str,
        feedback: Optional[str] = None,
    ) -> None:
        result = await session.execute(
            select(EpisodicEntry).where(
                EpisodicEntry.recommendation_id == recommendation_id
            )
        )
        entry = result.scalar_one_or_none()
        if entry:
            entry.outcome = outcome
            entry.user_feedback = feedback
            entry.updated_at = datetime.utcnow()
            await session.commit()

    async def get_history(
        self,
        session: AsyncSession,
        user_id: str,
        limit: int = 10,
    ) -> list[EpisodicEntry]:
        result = await session.execute(
            select(EpisodicEntry)
            .where(EpisodicEntry.user_id == user_id)
            .order_by(EpisodicEntry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def format_for_context(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> str:
        """
        Format episodic memory as a context string for the Venture Partner agent.
        Example output:
          - Jun 2025: Recommended 'AI Tutoring Bot'. Score: 7.8. Outcome: launched
          - May 2025: Recommended 'Freelance Design Marketplace'. Score: 6.2. Outcome: abandoned
        """
        entries = await self.get_history(session, user_id, limit=5)
        if not entries:
            return "No previous sessions found."

        lines = []
        for e in entries:
            outcome_str = e.outcome or "no feedback yet"
            lines.append(
                f"- {e.created_at.strftime('%b %Y')}: "
                f"Recommended '{e.recommended_idea}'. "
                f"Score: {e.startup_score}. "
                f"Outcome: {outcome_str}."
            )
        return "\n".join(lines)


async def create_tables():
    """Create DB tables. Call on app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
