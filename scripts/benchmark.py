"""
Board-vs-baseline benchmark: the SAME decision through (a) the full 7-agent board
(local backend, /api/analyze, live Qwen) and (b) one bare qwen-plus call with an
equivalent advisor prompt. Scores both on countable dimensions only — no human
judgment — and emits a markdown comparison table.

Usage (from repo root, backend running live on :8000):
    .venv/bin/python scripts/benchmark.py --case 1     # run one case, save raws + scores
    .venv/bin/python scripts/benchmark.py --table      # aggregate saved cases into RESULTS.md

Zero product-code imports beyond reading .env for the Qwen key (freeze holds).
"""

import argparse
import json
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "scripts" / "bench_results"
BACKEND = "http://localhost:8000"

# ── cases ─────────────────────────────────────────────────────────────────────

CASES = {
    1: {
        "name": "harborline-scaling",
        "company_id": "harborline-logistics",
        "profile": {
            "company_name": "Harborline Logistics",
            "sector": "regional cross-border logistics",
            "stage": "scaling",
            "business_model": "B2B freight + 3PL",
            "size_band": "11-50",
            "financials": {"revenue_band": "SGD 8-12M revenue", "margin": "~31% gross",
                           "cash_position": "16 months runway"},
        },
        "question": "Should we scale the Vietnam cross-border lane beyond the pilot?",
        "context": ("The Q4 2025 pilot ran asset-light via a partner. Volumes came in around "
                    "60% of plan - the larger anchor client delivered, the second under-shipped. "
                    "Margin stayed thin but positive. A third electronics shipper has asked for rates."),
        "budget": "SGD 300k", "timeline": "decide within 4 weeks",
        "options": ["Add a second Vietnam-side partner and dedicated capacity to scale the lane",
                    "Hold at pilot volume until a third anchor client signs a committed-volume contract"],
    },
    2: {
        "name": "bakery-central-kitchen",
        "company_id": "flourhouse-bakery",
        "profile": {
            "company_name": "Flourhouse Bakery",
            "sector": "artisan bakery and cafe",
            "stage": "established",
            "business_model": "two retail counters + wholesale to cafes",
            "size_band": "11-50",
            "financials": {"revenue_band": "SGD 1.5-2M revenue", "margin": "~52% gross",
                           "cash_position": "8 months runway"},
        },
        "question": "Should we move production to a central kitchen and close our two retail counters?",
        "context": ("Retail rents renew in 5 months at +20%. Wholesale is now 60% of revenue and "
                    "growing; the counters are flat. A central kitchen unit is available at half "
                    "the combined retail rent."),
        "budget": "SGD 120k fit-out", "timeline": "decide within 6 weeks",
        "options": None,
    },
    3: {
        "name": "itservices-fixed-price",
        "company_id": "meridian-systems",
        "profile": {
            "company_name": "Meridian Systems",
            "sector": "IT services and systems integration",
            "stage": "mature",
            "business_model": "time-and-materials consulting for enterprise clients",
            "size_band": "51-200",
            "financials": {"revenue_band": "SGD 15-20M revenue", "margin": "~24% gross",
                           "cash_position": "12 months runway"},
        },
        "question": "Should we switch our top five clients from time-and-materials to fixed-price contracts?",
        "context": ("Two of the five clients have asked for fixed pricing at renewal. Our delivery "
                    "estimates have historically run 15-30% over. Competitors are winning deals "
                    "on price certainty."),
        "budget": None, "timeline": "decide before the March renewal cycle",
        "options": None,
    },
}

BARE_SYSTEM = (
    "You are a business advisor. Given a company profile and one decision, produce a "
    "recommendation memo with a clear recommendation, rationale, options considered, "
    "risks, what information is missing, what would change your recommendation, and a plan."
)

# ── the two paths ─────────────────────────────────────────────────────────────

def profile_text(case) -> str:
    p, f = case["profile"], case["profile"]["financials"]
    lines = [f"Company: {p['company_name']}", f"Sector: {p['sector']}", f"Stage: {p['stage']}",
             f"Business model: {p['business_model']}", f"Size: {p['size_band']} employees",
             f"Revenue: {f['revenue_band']}", f"Margin: {f['margin']}", f"Cash: {f['cash_position']}"]
    if case.get("context"):
        lines.append(f"Context: {case['context']}")
    if case.get("budget"):
        lines.append(f"Budget: {case['budget']}")
    if case.get("timeline"):
        lines.append(f"Timeline: {case['timeline']}")
    if case.get("options"):
        lines.append("Options on the table: " + "; ".join(case["options"]))
    return "\n".join(lines)


def run_board(case) -> tuple[dict, float]:
    body = {
        "company_id": case["company_id"],
        "profile": case["profile"],
        "decision": {
            "question": case["question"], "context": case.get("context"),
            "constraints": {"budget": case.get("budget"), "timeline": case.get("timeline")},
            "options": case.get("options"),
        },
    }
    t0 = time.time()
    r = requests.post(f"{BACKEND}/api/analyze", json=body, timeout=420)
    r.raise_for_status()
    return r.json(), time.time() - t0


def run_bare(case) -> tuple[str, float]:
    # Key/base-url read the same way the backend reads them (.env at repo root).
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    from openai import OpenAI
    client = OpenAI(api_key=env["QWEN_API_KEY"],
                    base_url=env.get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"))
    user = f"{profile_text(case)}\n\nDecision: {case['question']}"
    t0 = time.time()
    resp = client.chat.completions.create(
        model="qwen-plus", max_tokens=6000,
        messages=[{"role": "system", "content": BARE_SYSTEM}, {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content, time.time() - t0

# ── countable scoring (same heuristics for both sides where no structure exists) ──

_STOP = set("""The A An If In On At Do Does Not No This That It They We Our Their Its As For With
Without While Should Could Would May Might Must However Conversely Only Once Hold Proceed
Conditional But And Or Then When Given Until Before After There These Those Both Each All Any Even
Also Yet Because Since So Add Legal Ops Verdict Case Critical Gap Strength Team Track Financial Org
Operational Recommendation Key Concerns Missing Risks Risk Execution Options Option Dissent What Why
How Market Pilot Phase Week Weeks Month Months Day Days Year Years Quarter Confirm Measure Review
Release Tie Hire Run Document Sign Validate Test Deploy Launch Board Chair Skeptic Scout Growth
Finance Capability Trend SGD USD KPI KPIs SLA SLAs SOP SOPs LOI LOIs MVC MVCs RFP RFPs ROI FX Q1 Q2
Q3 Q4 Plan Rationale Summary Decision Memo Advisor Business Company Client Clients Assumptions
Unknowns Information Immediate Secure Negotiate Monitor Set Use Leverage Focus Avoid Premature
Preserves Maintains Aligned Aligns Strong Solid Proven Limited Unclear Insufficient Lack Assess
Establish Ensure Allocate Begin Start Stop Cap Limit Define Mitigation Impact Objective Action
Actions Steps Next Overall Final Note Prepare Draft Model Build Retain Reduce Increase Consider
Evaluate Identify Communicate Transition Renewal Fixed Time Central Kitchen Wholesale Retail""".split())


def _input_vocab(case) -> set:
    src = profile_text(case) + " " + case["question"]
    return set(re.findall(r"[A-Z][a-zA-Z]+", src))


def invented_nouns(text: str, case) -> list[str]:
    allowed = _input_vocab(case) | _STOP
    found = {}
    for m in re.finditer(r"\b[A-Z][a-zA-Z]{2,}\b", text):
        t = m.group()
        if t in allowed or t.upper() == t:
            continue
        # sentence-initial words are grammar, not entities
        pre = text[max(0, m.start() - 2):m.start()]
        if not pre.strip() or pre.strip()[-1] in ".!?:;•-—*#\"'(":
            continue
        found[t] = found.get(t, 0) + 1
    return sorted(found)


def _bullets_under(text: str, heading_pat: str) -> int:
    """Count bullet lines in the section following a matching heading (markdown text)."""
    lines = text.splitlines()
    count, active = 0, False
    for ln in lines:
        if re.match(r"^\s{0,3}(#{1,6}|\*\*)", ln):
            active = bool(re.search(heading_pat, ln, re.I))
            continue
        if active and re.match(r"^\s*([-*•]|\d+[.)])\s+\S", ln):
            count += 1
    return count


def score_board(resp: dict, case) -> dict:
    rec = resp["recommendation"]
    prose = json.dumps(rec) + " " + " ".join(a.get("analysis", "") for a in resp["agent_outputs"])
    return {
        "risks": len(rec.get("risks", [])),
        "missing_inputs": len(rec.get("missing_inputs", [])),
        "dissent": len(rec.get("dissent", [])),
        "options_with_verdicts": sum(1 for o in rec.get("options_assessed", []) if o.get("verdict")),
        "reversal_conditions": 1 if rec.get("what_would_change_this_call", "").strip() else 0,
        "invented_nouns": len(invented_nouns(prose, case)),
        "confidence_calibration": 1 if rec.get("confidence") in ("low", "medium", "high") else 0,
    }


def score_bare(text: str, case) -> dict:
    risk = _bullets_under(text, r"risk")
    missing = _bullets_under(text, r"missing|unknown|information (needed|gaps)|assumption")
    options = _bullets_under(text, r"option")
    # verdicts attached to options: verdict words near "option" headings/bullets
    verdicts = len(re.findall(r"(?i)\b(recommended|favoured|favored|preferred|avoid|reject|viable|not recommended)\b", text))
    dissent = len(re.findall(r"(?i)\b(however|on the other hand|counter-?argument|devil'?s advocate|a skeptic|the case against|conversely)\b", text))
    reversal = 1 if re.search(r"(?i)(would change (my|the|this)|revisit (if|when)|reverse (course|this)|change (my|the) recommendation)", text) else 0
    confidence = 1 if re.search(r"(?i)\b(confidence[:\s]+(low|medium|high|moderate)|(low|medium|high|moderate) confidence)\b", text) else 0
    return {
        "risks": risk,
        "missing_inputs": missing,
        "dissent": dissent,
        "options_with_verdicts": min(options, verdicts) if options else (1 if verdicts else 0),
        "reversal_conditions": reversal,
        "invented_nouns": len(invented_nouns(text, case)),
        "confidence_calibration": confidence,
    }

# ── table ─────────────────────────────────────────────────────────────────────

DIMS = [
    ("risks", "Distinct risks identified", "higher"),
    ("missing_inputs", "Missing inputs / unknowns named", "higher"),
    ("dissent", "Dissent / counter-arguments surfaced", "higher"),
    ("options_with_verdicts", "Options assessed with verdicts", "higher"),
    ("reversal_conditions", "Concrete reversal conditions", "higher"),
    ("invented_nouns", "Invented proper nouns (entities)", "lower"),
    ("confidence_calibration", "Confidence calibration present", "higher"),
]


def write_table():
    rows = []
    cases = []
    for i in sorted(CASES):
        f = OUT / f"case{i}_scores.json"
        if f.exists():
            cases.append((i, json.loads(f.read_text())))
    md = ["# Board vs single-agent baseline — countable dimensions", ""]
    md.append("Same decision, two paths: full 7-agent board (`/api/analyze`, live) vs one bare "
              "`qwen-plus` call with an equivalent advisor prompt. Counts only; no human judgment.")
    md.append("")
    header = "| Dimension (want) |" + "".join(
        f" {CASES[i]['name']} board | bare |" for i, _ in cases) + " total board | total bare |"
    sep = "|---|" + "---|" * (2 * len(cases) + 2)
    md += [header, sep]
    for key, label, want in DIMS:
        row = f"| {label} ({want}) |"
        tb = ta = 0
        for _, s in cases:
            b, a = s["board"][key], s["bare"][key]
            tb, ta = tb + b, ta + a
            row += f" {b} | {a} |"
        row += f" **{tb}** | **{ta}** |"
        md.append(row)
    md.append("")
    for i, s in cases:
        md.append(f"- case{i} ({CASES[i]['name']}): board {s['board_secs']:.0f}s, "
                  f"bare {s['bare_secs']:.0f}s; invented nouns board={s['board_invented']}, "
                  f"bare={s['bare_invented']}")
    (OUT / "RESULTS.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


def run_case(i: int):
    case = CASES[i]
    OUT.mkdir(parents=True, exist_ok=True)
    board, bsecs = run_board(case)
    (OUT / f"case{i}_board.json").write_text(json.dumps(board, indent=2))
    bare, asecs = run_bare(case)
    (OUT / f"case{i}_bare.md").write_text(bare)
    sb, sa = score_board(board, case), score_bare(bare, case)
    prose = json.dumps(board["recommendation"]) + " " + " ".join(a.get("analysis", "") for a in board["agent_outputs"])
    scores = {
        "board": sb, "bare": sa, "board_secs": bsecs, "bare_secs": asecs,
        "board_invented": invented_nouns(prose, case),
        "bare_invented": invented_nouns(bare, case),
    }
    (OUT / f"case{i}_scores.json").write_text(json.dumps(scores, indent=2))
    print(f"case{i} done: board {bsecs:.0f}s {sb} | bare {asecs:.0f}s {sa}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", type=int)
    ap.add_argument("--table", action="store_true")
    args = ap.parse_args()
    if args.case:
        run_case(args.case)
    if args.table:
        write_table()
