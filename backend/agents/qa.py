import json
from typing import Dict, Any

from .base import BaseAgent
from ..llm.provider import DEEP_MODEL
from ..models import CompanyProfile, AgentOutput

SYSTEM_PROMPT = """\
You are the QA Engineer on an AI product-delivery loop. You receive a Senior SWE's build spec
and review it BEFORE anything ships. You are the last gate: hunt for bugs, data leaks, possible
data breaches, and gaps (missing steps, untested paths, undefined behaviour).

Rules:
- Verdict "pass" ONLY when you would stake the release on it — no open high/medium issues.
- Every issue must point at a specific part of the spec (location) and say why it is a problem.
- Data handling is your priority: anything that stores, logs, or transmits user data without a
  stated safeguard is a leak or breach issue, not a nit.
- Do not invent requirements the theme never asked for; flag real problems only.

Respond with valid JSON only:
{
  "verdict": "pass | fail",
  "issues": [
    {
      "severity": "high | medium | low",
      "category": "bug | leak | breach | gap",
      "description": "what is wrong and why it matters",
      "location": "which spec section/step"
    }
  ],
  "review_summary": "one-paragraph plain-language verdict"
}"""

# Call-counted fixtures: round 1 fails on the two planted problems in the SWE's
# v1 spec (verbatim feedback in logs; no rate limit); round 2 passes the v2 fix.

_MOCK_FAIL = json.dumps({
    "verdict": "fail",
    "issues": [
        {
            "severity": "high",
            "category": "leak",
            "description": (
                "The spec logs each matched feedback note's full text verbatim for keyword "
                "tuning. Feedback notes contain unredacted operator-submitted detail (names, "
                "lanes, customers) — writing them to logs is a PII leak and would surface in "
                "any log export or breach."
            ),
            "location": "implementation_steps[1] / data_touched[1]",
        },
        {
            "severity": "medium",
            "category": "bug",
            "description": (
                "The new checklist path is not covered by any rate limit. Every other "
                "pipeline entry point is rate-limited; an uncapped path invites abuse and "
                "cost blowout on the live model."
            ),
            "location": "security_considerations",
        },
    ],
    "review_summary": (
        "Fail. The feature itself is sound, but verbatim feedback logging is a data leak "
        "waiting for a log export, and the new path skips the rate-limit discipline the rest "
        "of the API follows. Both must be fixed before release."
    ),
})

_MOCK_PASS = json.dumps({
    "verdict": "pass",
    "issues": [],
    "review_summary": (
        "Pass. The revision removed verbatim feedback from logs (anonymised category counts "
        "only), added a leak regression test, and put the checklist path under the existing "
        "rate limit. No open issues — safe to release."
    ),
})


class QAEngineerAgent(BaseAgent):
    name = "qa_engineer"
    role = "QA Engineer — reviews the build spec for bugs, leaks, and breach vectors"
    llm_model = DEEP_MODEL
    max_tokens = 3000

    def __init__(self):
        super().__init__()
        self._mock_calls = 0                   # fail first, pass on the revised spec

    def _mock_response(self) -> str:
        return _MOCK_FAIL if self._mock_calls <= 1 else _MOCK_PASS

    def analyze(self, profile: CompanyProfile, context: Dict[str, Any] = {}) -> AgentOutput:
        self._mock_calls += 1
        spec: Dict[str, Any] = context.get("spec", {})

        if self.mock:
            raw = self._parse_json(self._mock_response())
        else:
            user_msg = (
                f"Build spec under review (round {context.get('round', 1)}):\n"
                f"{json.dumps(spec, indent=2)}\n\n"
                "Review it. Verdict + issues."
            )
            raw = self._parse_json(self._call_llm(SYSTEM_PROMPT, user_msg))

        issues = raw.get("issues", [])
        return AgentOutput(
            agent_name=self.name,
            role=self.role,
            analysis=raw.get("review_summary", ""),
            key_findings=[f"Verdict: {raw.get('verdict', 'fail')}"],
            concerns=[i.get("description", "") for i in issues if isinstance(i, dict)],
            recommendations=[],
            raw_data=raw,
        )
