"""
Vault store — file-backed implementation of the frozen vault interface.

Layout under VAULT_PATH:
    <vault_root>/
        <company_id>/
            _index.md            # optional human-readable index (regenerated)
            2026-07-01-vietnam-expansion.md
            ...

Each decision note is markdown with YAML frontmatter:
    ---
    type: decision
    decision_id: <uuid>
    date: 2026-07-01
    recommendation: conditional
    confidence: medium
    outcome:               # filled later by write_back on feedback
    summary: One-line summary the selector ranks on.
    ---
    ## Decision
    ...body...

Retrieval (read) selects the relevant notes for a query. Selection is LLM-driven
when a key is present; in mock mode (or with a tiny vault) it falls back to a
deterministic keyword-overlap heuristic. Either way it only ever loads the bodies
of the SELECTED notes — never the whole vault.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..config import settings
from ..models import (
    CompanyProfile,
    Decision,
    BoardRecommendation,
    BuildSpec,
    VaultNote,
    ContextBundle,
    FeedbackNote,
)

# How many notes the selector is allowed to pull into context per run.
MAX_SELECTED_NOTES = 4

# The company-identity note. Underscore-prefixed DELIBERATELY: index() skips
# `_*` files, so the profile is never ranked by the selector and never counts
# against MAX_SELECTED_NOTES — it is not a rankable memory, it is who the
# company is. read() loads it explicitly and always includes it in the
# ContextBundle as company-identity context.
PROFILE_NOTE = "_profile.md"

# Stable "- Label: attr" lines — the render/parse round-trip for hydration.
_PROFILE_LINES: list[tuple[str, str]] = [
    ("Company name", "company_name"),
    ("Sector", "sector"),
    ("Stage", "stage"),
    ("Business model", "business_model"),
    ("Size band", "size_band"),
    ("Revenue band", "financials.revenue_band"),
    ("Margin", "financials.margin"),
    ("Cash position", "financials.cash_position"),
]

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
_STOPWORDS = {
    "the", "a", "an", "to", "of", "and", "or", "for", "in", "on", "we",
    "our", "should", "is", "are", "this", "that", "with", "into", "next",
}


_MAX_SLUG_LEN = 60


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if len(slug) > _MAX_SLUG_LEN:
        cut = slug[:_MAX_SLUG_LEN]
        # Never cut mid-word: if the cap lands inside a word, drop that word.
        if slug[_MAX_SLUG_LEN] != "-" and "-" in cut:
            cut = cut.rsplit("-", 1)[0]
        slug = cut.rstrip("-")
    return slug or "decision"


def _get_profile_field(profile: CompanyProfile, dotted: str) -> str:
    obj = profile
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj or ""


def _render_profile_body(profile: CompanyProfile) -> str:
    lines = "\n".join(
        f"- {label}: {_get_profile_field(profile, attr)}"
        for label, attr in _PROFILE_LINES
    )
    return f"# {profile.company_name} — company profile\n\n{lines}"


def _parse_profile_body(body: str) -> Optional[CompanyProfile]:
    """Invert _render_profile_body. Returns None if the note isn't parseable."""
    values: dict = {}
    for label, attr in _PROFILE_LINES:
        m = re.search(rf"^- {re.escape(label)}:[ \t]*(.*)$", body, re.MULTILINE)
        values[attr] = m.group(1).strip() if m else ""
    if not values.get("company_name"):
        return None
    return CompanyProfile(
        company_name=values["company_name"],
        sector=values["sector"],
        stage=values["stage"],
        business_model=values["business_model"],
        size_band=values["size_band"],
        financials={
            "revenue_band": values["financials.revenue_band"],
            "margin": values["financials.margin"] or None,
            "cash_position": values["financials.cash_position"] or None,
        },
    )


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Minimal YAML-frontmatter parser (flat key: value only — no deps)."""
    m = _FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw.strip()
    fm_block, body = m.group(1), m.group(2)
    fm: dict = {}
    for line in fm_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body.strip()


def _dump_frontmatter(fm: dict) -> str:
    lines = ["---"]
    for key, val in fm.items():
        lines.append(f"{key}: {val if val is not None else ''}")
    lines.append("---")
    return "\n".join(lines)


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS}


class Vault:
    """File-backed vault rooted at VAULT_PATH. One folder per company_id."""

    def __init__(self, root: Optional[str] = None):
        self.root = Path(root or settings.vault_path)

    # ── paths ────────────────────────────────────────────────────────────
    def _company_dir(self, company_id: str) -> Path:
        if not re.fullmatch(r'[a-z0-9][a-z0-9\-_]{0,49}', company_id):
            raise ValueError(f"Invalid company_id: {company_id!r}")
        result = (self.root / company_id).resolve()
        try:
            result.relative_to(self.root.resolve())
        except ValueError:
            raise ValueError("Path traversal attempt blocked")
        return result

    # ── index ────────────────────────────────────────────────────────────
    def index(self, company_id: str) -> List[VaultNote]:
        """Build the lightweight index the selector ranks on (never reads bodies)."""
        company_dir = self._company_dir(company_id)
        if not company_dir.exists():
            return []
        notes: List[VaultNote] = []
        for path in sorted(company_dir.glob("*.md")):
            if path.name.startswith("_"):
                continue
            try:
                fm, _body = _parse_frontmatter(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            # Decision notes ONLY: feedback notes are read via read_feedback(),
            # release notes via the delivery loop — neither belongs in the
            # decision-context index the selector ranks or the history endpoint.
            if fm.get("type") != "decision":
                continue
            notes.append(VaultNote(
                path=path.name,
                frontmatter=fm,
                summary=fm.get("summary", ""),
            ))
        return notes

    # ── profile (company identity) ───────────────────────────────────────
    def write_profile(self, company_id: str, profile: CompanyProfile) -> None:
        """Create _profile.md on first write; overwrite only when fields changed."""
        existing = self.read_profile(company_id)
        if existing is not None and existing == profile:
            return
        company_dir = self._company_dir(company_id)
        company_dir.mkdir(parents=True, exist_ok=True)
        fm = {
            "type": "profile",
            "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        (company_dir / PROFILE_NOTE).write_text(
            f"{_dump_frontmatter(fm)}\n\n{_render_profile_body(profile)}\n",
            encoding="utf-8",
        )

    def read_profile(self, company_id: str) -> Optional[CompanyProfile]:
        """Parse _profile.md back into a CompanyProfile (None if absent/unparseable)."""
        path = self._company_dir(company_id) / PROFILE_NOTE
        if not path.exists():
            return None
        try:
            _fm, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            return None
        return _parse_profile_body(body)

    # ── read (selective retrieval) ───────────────────────────────────────
    def read(self, company_id: str, query: str) -> ContextBundle:
        """Select the notes relevant to `query` and return only their bodies.

        The company profile (_profile.md) is not part of selection: it is always
        included first when present, as identity context outside the
        MAX_SELECTED_NOTES budget.

        Single filesystem pass: profile body and index entries are collected in one
        glob walk to avoid two separate directory scans per board run.
        """
        notes, used = [], []
        company_dir = self._company_dir(company_id)
        if not company_dir.exists():
            return ContextBundle(notes=notes, used_paths=used)

        index_entries: List[VaultNote] = []
        for path in sorted(company_dir.glob("*.md")):
            if path.name == PROFILE_NOTE:
                try:
                    _fm, pbody = _parse_frontmatter(path.read_text(encoding="utf-8"))
                    notes.append(pbody)
                    used.append(PROFILE_NOTE)
                except OSError:
                    pass
                continue
            if path.name.startswith("_"):
                continue
            try:
                fm, _body = _parse_frontmatter(path.read_text(encoding="utf-8"))
            except OSError:
                continue
            if fm.get("type") != "decision":
                continue
            index_entries.append(VaultNote(
                path=path.name,
                frontmatter=fm,
                summary=fm.get("summary", ""),
            ))

        if index_entries:
            selected = self._select(index_entries, query)
            for note in selected:
                try:
                    _fm, body = _parse_frontmatter(
                        (company_dir / note.path).read_text(encoding="utf-8")
                    )
                except OSError:
                    continue
                notes.append(body)
                used.append(note.path)
        return ContextBundle(notes=notes, used_paths=used)

    def _select(self, index: List[VaultNote], query: str) -> List[VaultNote]:
        """Rank the index against the query.

        Live mode asks the LLM to pick relevant filenames; mock mode (and any
        selector failure) falls back to keyword overlap on frontmatter+summary.
        Both cap at MAX_SELECTED_NOTES so context never balloons.
        """
        if settings.is_live and len(index) > MAX_SELECTED_NOTES:
            try:
                return self._llm_select(index, query)
            except Exception:
                pass  # never let retrieval crash the pipeline — fall through
        return self._keyword_select(index, query)

    def _keyword_select(self, index: List[VaultNote], query: str) -> List[VaultNote]:
        q = _tokens(query)
        scored = []
        for note in index:
            hay = f"{note.path} {note.summary} {' '.join(str(v) for v in note.frontmatter.values())}"
            overlap = len(q & _tokens(hay))
            scored.append((overlap, note))
        # Highest overlap first; ties keep filename order (dates sort chronologically).
        scored.sort(key=lambda t: t[0], reverse=True)
        ranked = [n for score, n in scored if score > 0]
        # If nothing overlaps, fall back to the most recent notes so history still shows.
        chosen = ranked or [n for _s, n in scored]
        return chosen[:MAX_SELECTED_NOTES]

    def _llm_select(self, index: List[VaultNote], query: str) -> List[VaultNote]:
        """Ask the LLM which notes to load, given only the index (not the bodies)."""
        from ..llm.provider import QwenProvider, FAST_MODEL

        catalog = "\n".join(
            f"{i}. {n.path} — {n.summary or n.frontmatter.get('type', 'note')}"
            for i, n in enumerate(index)
        )
        system = (
            "You select which past board notes are relevant to a new decision. "
            "Return valid JSON only: {\"indices\": [int, ...]} — at most "
            f"{MAX_SELECTED_NOTES} indices, most relevant first."
        )
        user = f"New decision / query:\n{query}\n\nAvailable notes:\n{catalog}"
        raw = QwenProvider(model=FAST_MODEL).chat(system, user, max_tokens=300)
        import json
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        picked = json.loads(m.group()) if m else {"indices": []}
        idxs = [i for i in picked.get("indices", []) if 0 <= i < len(index)]
        selected = [index[i] for i in idxs][:MAX_SELECTED_NOTES]
        return selected or self._keyword_select(index, query)

    # ── write_back (append + outcome loop) ───────────────────────────────
    def write_back(
        self,
        company_id: str,
        decision: Decision,
        recommendation: BoardRecommendation,
        learnings: Optional[List[str]] = None,
        profile: Optional[CompanyProfile] = None,
        response_id: str = "",
    ) -> str:
        """Append a decision note and return its decision_id (used by the outcome loop).

        response_id is stored in the frontmatter so the outcome loop can find the
        note again after a restart wipes the in-memory response store.
        """
        company_dir = self._company_dir(company_id)
        company_dir.mkdir(parents=True, exist_ok=True)

        # Persist company identity alongside the decision (created on the first
        # write, refreshed when the operator sends a changed profile).
        if profile is not None:
            self.write_profile(company_id, profile)

        decision_id = str(uuid.uuid4())
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        summary = f"{decision.question} → {recommendation.recommendation} ({recommendation.confidence})"
        fm = {
            "type": "decision",
            "decision_id": decision_id,
            "response_id": response_id,
            "date": date,
            "recommendation": recommendation.recommendation,
            "confidence": recommendation.confidence,
            "outcome": "",   # filled later by record_outcome
            "summary": summary.replace("\n", " ")[:200],
        }

        learn_lines = "\n".join(f"- {l}" for l in (learnings or [])) or "- (none recorded)"
        dissent_lines = "\n".join(
            f"- **{d.agent}**: {d.position}" for d in recommendation.dissent
        ) or "- (none)"
        body = (
            f"## Decision\n{decision.question}\n\n"
            f"### Context\n{decision.context or '(none)'}\n\n"
            f"## Recommendation: {recommendation.recommendation} "
            f"(confidence: {recommendation.confidence})\n{recommendation.rationale}\n\n"
            f"### What would change this call\n{recommendation.what_would_change_this_call}\n\n"
            f"### Dissent on record\n{dissent_lines}\n\n"
            f"### Missing inputs\n"
            + ("\n".join(f"- {mi}" for mi in recommendation.missing_inputs) or "- (none)")
            + f"\n\n### Learnings\n{learn_lines}\n\n"
            f"### Outcome\n(pending — updated when the operator reports back)\n"
        )

        # Suffix with the decision_id so two same-day decisions with an identical
        # question don't collide on filename (which would overwrite the earlier
        # note and orphan its decision_id from the outcome loop).
        filename = f"{date}-{_slugify(decision.question)}-{decision_id[:8]}.md"
        (company_dir / filename).write_text(
            f"{_dump_frontmatter(fm)}\n\n{body}", encoding="utf-8"
        )
        return decision_id

    def record_outcome(self, company_id: str, decision_id: str,
                       outcome: str, notes: str = "") -> bool:
        """Write a real outcome back against the matching decision note (the loop)."""
        company_dir = self._company_dir(company_id)
        if not company_dir.exists():
            return False
        for path in company_dir.glob("*.md"):
            if path.name.startswith("_"):
                continue
            try:
                raw = path.read_text(encoding="utf-8")
            except OSError:
                continue
            fm, body = _parse_frontmatter(raw)
            if fm.get("decision_id") == decision_id:
                fm["outcome"] = (outcome or "").replace("\n", " ")[:120]
                outcome_block = (
                    f"### Outcome\n**{outcome}**\n\n{notes}\n" if outcome
                    else "### Outcome\n(pending)\n"
                )
                body = re.sub(r"### Outcome\n.*$", outcome_block, body, flags=re.DOTALL)
                path.write_text(f"{_dump_frontmatter(fm)}\n\n{body}", encoding="utf-8")
                return True
        return False

    def write_release(self, company_id: str, spec: BuildSpec, theme: str) -> str:
        """Write a `type: release` note for a feature that cleared the QA loop.

        Release notes are delivery-loop provenance, not board memory: index()/read()
        include only `type: decision`, so they never enter decision retrieval. The
        uuid suffix keeps same-day releases distinct AND matches the .gitignore
        rule for runtime write-backs. Returns the filename.
        """
        company_dir = self._company_dir(company_id)
        company_dir.mkdir(parents=True, exist_ok=True)

        release_id = str(uuid.uuid4())
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        fm = {
            "type": "release",
            "release_id": release_id,
            "date": date,
            "feature": spec.feature_name.replace("\n", " ")[:120],
            "theme": theme.replace("\n", " ")[:120],
            "summary": f"Released: {spec.feature_name} (from feedback theme: {theme})"[:200],
        }

        def _section(title: str, items: List[str]) -> str:
            lines = "\n".join(f"- {i}" for i in items) or "- (none)"
            return f"### {title}\n{lines}\n"

        body = (
            f"## Released feature: {spec.feature_name}\n\n"
            f"**From feedback theme:** {theme}\n\n"
            f"**Problem:** {spec.problem}\n\n"
            + _section("Scope", spec.scope)
            + "\n" + _section("Out of scope", spec.out_of_scope)
            + "\n" + _section("Data touched", spec.data_touched)
            + "\n" + _section("Implementation steps", spec.implementation_steps)
            + "\n" + _section("Security considerations", spec.security_considerations)
            + "\n" + _section("QA verified", spec.test_notes)
        )

        filename = f"release-{date}-{_slugify(spec.feature_name)}-{release_id[:8]}.md"
        (company_dir / filename).write_text(
            f"{_dump_frontmatter(fm)}\n\n{body}", encoding="utf-8"
        )
        return filename

    def find_by_response_id(self, response_id: str) -> Optional[tuple[str, str]]:
        """Locate the decision note written for a response → (company_id, decision_id).

        Fallback for the outcome loop when the in-memory response store was wiped
        by a restart — the vault note is the durable record. Walks every company
        folder's frontmatter (small vaults; bodies are never read).
        """
        if not response_id or not self.root.exists():
            return None
        for company_dir in sorted(self.root.iterdir()):
            if not company_dir.is_dir():
                continue
            for path in company_dir.glob("*.md"):
                if path.name.startswith("_"):
                    continue
                try:
                    fm, _body = _parse_frontmatter(path.read_text(encoding="utf-8"))
                except OSError:
                    continue
                if fm.get("response_id") == response_id and fm.get("decision_id"):
                    return company_dir.name, fm["decision_id"]
        return None

    def read_feedback(self, company_id: str) -> List[FeedbackNote]:
        """Return all notes with frontmatter type=feedback for this company.

        Follows the same folder-walk + frontmatter-parse pattern as index(), but
        filters on type == 'feedback' and returns FeedbackNote objects rather than
        VaultNote index entries. Returns [] gracefully when no notes exist.
        """
        company_dir = self._company_dir(company_id)
        if not company_dir.exists():
            return []
        notes: List[FeedbackNote] = []
        for path in sorted(company_dir.glob("*.md")):
            if path.name.startswith("_"):
                continue
            try:
                raw = path.read_text(encoding="utf-8")
            except OSError:
                continue
            fm, body = _parse_frontmatter(raw)
            if fm.get("type") != "feedback":
                continue
            notes.append(FeedbackNote(
                text=body.strip(),
                date=fm.get("date", ""),
                response_id=fm.get("response_id", ""),
            ))
        return notes

    def history(self, company_id: str) -> List[dict]:
        """The company's decision history from the index (for GET /api/company/{id})."""
        return [
            {"path": n.path, **n.frontmatter}
            for n in sorted(self.index(company_id),
                            key=lambda n: n.frontmatter.get("date", ""), reverse=True)
        ]


# Module-level singleton + contract-shaped functions (what the graph/API import).
_vault = Vault()


def read(company_id: str, query: str) -> ContextBundle:
    return _vault.read(company_id, query)


def write_back(company_id: str, decision: Decision,
               recommendation: BoardRecommendation,
               learnings: Optional[List[str]] = None,
               profile: Optional[CompanyProfile] = None,
               response_id: str = "") -> str:
    return _vault.write_back(company_id, decision, recommendation, learnings, profile, response_id)


def find_by_response_id(response_id: str) -> Optional[tuple[str, str]]:
    return _vault.find_by_response_id(response_id)


def write_release(company_id: str, spec: BuildSpec, theme: str) -> str:
    return _vault.write_release(company_id, spec, theme)


def read_profile(company_id: str) -> Optional[CompanyProfile]:
    return _vault.read_profile(company_id)


def record_outcome(company_id: str, decision_id: str, outcome: str, notes: str = "") -> bool:
    return _vault.record_outcome(company_id, decision_id, outcome, notes)


def history(company_id: str) -> List[dict]:
    return _vault.history(company_id)


def read_feedback(company_id: str) -> List[FeedbackNote]:
    return _vault.read_feedback(company_id)
