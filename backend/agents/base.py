import json
import re
from typing import Dict, Any
from ..config import settings
from ..models import CompanyProfile, Decision, AgentOutput
from ..llm.provider import QwenProvider, FAST_MODEL


class BaseAgent:
    """
    Base class for all FounderOS agents.

    An agent evaluates ONE decision brought by an existing company. Subclasses set
    `llm_model` to control model tiering:
      - FAST_MODEL (qwen-turbo)  — Scout, Trend, Finance, Growth
      - DEEP_MODEL (qwen-plus)   — Skeptic, Capability, Chair (venture_partner)
    """

    name: str = "Base Agent"
    role: str = "Base"
    llm_model: str = FAST_MODEL  # override in subclass for reasoning-heavy agents
    max_tokens: int = 2000       # override for agents whose JSON output is large
                                 # (Skeptic, VP) — too low truncates JSON in live mode

    def __init__(self):
        self.mock = settings.use_mock_llm or not settings.qwen_api_key
        self.provider = QwenProvider(model=self.llm_model)

    # ──────────────────────────────────────────
    # Core LLM Call
    # ──────────────────────────────────────────

    def _call_llm(self, system: str, user: str, max_tokens: int | None = None) -> str:
        """Return mock fixture or live Qwen response depending on config.

        max_tokens defaults to the agent's class-level `max_tokens` so each agent
        controls its own ceiling; pass an explicit value to override per call.
        """
        if self.mock:
            return self._mock_response()
        return self.provider.chat(system, user, max_tokens or self.max_tokens)

    def _mock_response(self) -> str:
        """Override in each subclass with a realistic fixture for mock mode."""
        return json.dumps({"mock": True, "agent": self.name})

    # ──────────────────────────────────────────
    # JSON Parsing
    # ──────────────────────────────────────────

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from a Qwen response, handling markdown fences."""
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            text = fence_match.group(1)
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            raise ValueError(
                f"[{self.name}] Failed to parse JSON response.\n"
                f"Error: {e}\nRaw text (first 400 chars):\n{text[:400]}"
            )

    # ──────────────────────────────────────────
    # Company + Decision Formatters (shared by all agents)
    # ──────────────────────────────────────────

    def _format_company(self, profile: CompanyProfile) -> str:
        fin = profile.financials
        fin_line = ", ".join(
            part for part in (
                f"revenue {fin.revenue_band}" if fin.revenue_band else "",
                f"margin {fin.margin}" if fin.margin else "",
                f"cash {fin.cash_position}" if fin.cash_position else "",
            ) if part
        ) or "not disclosed"
        return (
            f"Company Profile:\n"
            f"- Name: {profile.company_name}\n"
            f"- Sector: {profile.sector}\n"
            f"- Stage: {profile.stage}\n"
            f"- Business model: {profile.business_model}\n"
            f"- Size: {profile.size_band} employees\n"
            f"- Financials: {fin_line}\n"
        )

    def _format_decision(self, decision: Decision) -> str:
        c = decision.constraints
        constraint_line = ", ".join(
            part for part in (
                f"budget {c.budget}" if c.budget else "",
                f"timeline {c.timeline}" if c.timeline else "",
            ) if part
        ) or "none stated"
        opts = "\n".join(f"  - {o}" for o in (decision.options or [])) or "  (none — frame them)"
        return (
            f"Decision on the table:\n"
            f"- Question: {decision.question}\n"
            f"- Context: {decision.context or '(none provided)'}\n"
            f"- Constraints: {constraint_line}\n"
            f"- Options under consideration:\n{opts}\n"
        )

    def _format_options(self, options: list) -> str:
        return "\n".join(f"- {o}" for o in options) if options else "- (Scout will frame options)"

    def _format_research_brief(self, context: Dict[str, Any]) -> str:
        """Render the Research agent's market-intelligence brief for a prompt, if present.

        Returns an empty string when no brief is available, so an agent's prompt is
        unchanged from today's behaviour when Research produced nothing.
        """
        brief = context.get("research_brief", "")
        return f"\n## Market Intelligence Brief\n{brief}\n" if brief else ""

    # ──────────────────────────────────────────
    # Override in subclasses
    # ──────────────────────────────────────────

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        raise NotImplementedError("Each agent must implement analyze()")
