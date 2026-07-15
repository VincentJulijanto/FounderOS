import json
from typing import Dict, Any, List

from .base import BaseAgent
from ..llm.provider import DEEP_MODEL
from ..models import CompanyProfile, AgentOutput

SYSTEM_PROMPT = """\
You are the Senior Software Engineer on an AI product-delivery loop. You receive one validated
feedback theme (a user need with representative quotes) and produce a BUILD SPEC — the document
QA will review before anything ships. On revision rounds you also receive QA's issues; your
revised spec must address EVERY issue explicitly (fix it in the relevant section, or record it
in out_of_scope with a reason).

Rules:
- Be concrete: name the data the feature reads/stores, the steps to build it, and how it is tested.
- Treat user data conservatively — call out anything that touches PII, logs, or third parties in
  security_considerations.
- Never invent names, companies, products, or agreements not present in the input.

Respond with valid JSON only:
{
  "feature_name": "string",
  "problem": "string — the user need this answers",
  "scope": ["what is included"],
  "out_of_scope": ["what is deliberately excluded, with reason"],
  "data_touched": ["each data element read or stored"],
  "implementation_steps": ["ordered build steps"],
  "security_considerations": ["how leaks/breaches/abuse are prevented"],
  "test_notes": ["what QA should verify"]
}"""

# Deterministic two-version fixture pair so mock mode exercises the full loop:
# v1 carries a plantable leak (raw feedback text in logs) and no rate limit —
# exactly the two issues the QA mock flags; v2 fixes both.

_MOCK_V1 = json.dumps({
    "feature_name": "Operational risk pre-flight check",
    "problem": (
        "Users report that board memos miss operational risk factors (port congestion, "
        "customs lead times) that materially affect cross-border decisions."
    ),
    "scope": [
        "A pre-debate checklist step that scans the decision for transport-mode keywords",
        "Auto-inject a structured operational-risk section into the Skeptic's context",
        "Surface unaddressed operational risks in the memo's missing_inputs",
    ],
    "out_of_scope": [
        "Vendor or software recommendations — outside the board's mandate",
    ],
    "data_touched": [
        "Decision question and context (request body)",
        "Raw user feedback notes, logged verbatim for tuning the keyword list",
    ],
    "implementation_steps": [
        "Add an operational-risk keyword map per sector to the Scout stage",
        "Log each matched feedback note's full text to the tuning log",
        "Extend the Skeptic prompt with the matched risk categories",
        "Render unaddressed categories under missing_inputs in the memo",
    ],
    "security_considerations": [
        "Feature runs server-side only; no new endpoints exposed",
    ],
    "test_notes": [
        "Cross-border decision triggers the congestion + customs categories",
        "Non-logistics decision adds no operational-risk section",
    ],
})

_MOCK_V2 = json.dumps({
    "feature_name": "Operational risk pre-flight check",
    "problem": (
        "Users report that board memos miss operational risk factors (port congestion, "
        "customs lead times) that materially affect cross-border decisions."
    ),
    "scope": [
        "A pre-debate checklist step that scans the decision for transport-mode keywords",
        "Auto-inject a structured operational-risk section into the Skeptic's context",
        "Surface unaddressed operational risks in the memo's missing_inputs",
    ],
    "out_of_scope": [
        "Vendor or software recommendations — outside the board's mandate",
        "Verbatim feedback logging — removed after QA flagged it as a PII leak; the keyword "
        "list is tuned from anonymised category counts instead",
    ],
    "data_touched": [
        "Decision question and context (request body)",
        "Anonymised category counts derived from feedback notes (no raw text stored)",
    ],
    "implementation_steps": [
        "Add an operational-risk keyword map per sector to the Scout stage",
        "Aggregate matched categories into anonymised counts (no verbatim feedback in logs)",
        "Extend the Skeptic prompt with the matched risk categories",
        "Render unaddressed categories under missing_inputs in the memo",
        "Apply the existing per-route rate limit to the new checklist path",
    ],
    "security_considerations": [
        "Feature runs server-side only; no new endpoints exposed",
        "No verbatim user feedback is written to logs — category counts only",
        "Checklist path inherits the analyze route's rate limit",
    ],
    "test_notes": [
        "Cross-border decision triggers the congestion + customs categories",
        "Non-logistics decision adds no operational-risk section",
        "Log output contains no raw feedback text (leak regression test)",
    ],
})


class SeniorSWEAgent(BaseAgent):
    name = "senior_swe"
    role = "Senior SWE — turns a validated feedback theme into a build spec"
    llm_model = DEEP_MODEL
    max_tokens = 6000                          # full spec JSON is large

    def __init__(self):
        super().__init__()
        self._mock_calls = 0                   # v1 first, fixed v2 on revision rounds

    def _mock_response(self) -> str:
        return _MOCK_V1 if self._mock_calls <= 1 else _MOCK_V2

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        self._mock_calls += 1
        theme: Dict[str, Any] = context.get("theme", {})
        previous_spec: Dict[str, Any] = context.get("previous_spec", {})
        qa_issues: List[Dict[str, Any]] = context.get("qa_issues", [])

        if self.mock:
            raw = self._parse_json(self._mock_response())
        else:
            parts = [
                f"{self._format_company(profile)}\n"
                f"Validated feedback theme:\n{json.dumps(theme, indent=2)}",
            ]
            if previous_spec:
                parts.append(
                    f"Your previous spec:\n{json.dumps(previous_spec, indent=2)}\n\n"
                    f"QA found these issues — your revised spec must address every one:\n"
                    f"{json.dumps(qa_issues, indent=2)}"
                )
                parts.append("Produce the REVISED build spec.")
            else:
                parts.append("Produce the build spec for this theme.")
            raw = self._parse_json(self._call_llm(SYSTEM_PROMPT, "\n\n".join(parts)))

        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=f"{raw.get('feature_name', '')}: {raw.get('problem', '')}",
            key_findings=raw.get("scope", []),
            concerns=raw.get("security_considerations", []),
            recommendations=raw.get("implementation_steps", []),
            raw_data=raw,
        )
