"""Optional OpenAI-compatible enhancement; the app never requires this module's API access.

When AI_ENHANCEMENT_ENABLED=true and OPENAI_API_KEY is configured, this sends a
small, redacted assessment summary to the configured chat-completions endpoint.
Any failure returns the local report unchanged.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parent


def _load_env_file() -> None:
    path = BASE_DIR / ".env"
    if not path.exists():
        return
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"\''))
    except OSError:
        return


def enhance_report_if_configured(data: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    _load_env_file()
    if os.getenv("AI_ENHANCEMENT_ENABLED", "false").lower() not in {"1", "true", "yes"}:
        return report
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return report

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    payload_context = {
        "idea_name": data.get("idea_name"),
        "industry": data.get("industry"),
        "description": data.get("description"),
        "problem": data.get("problem"),
        "solution": data.get("solution"),
        "target_customers": data.get("target_customers"),
        "geographic_market": data.get("geographic_market"),
        "uvp": data.get("uvp"),
        "competitors_as_entered_by_founder": data.get("competitors"),
        "revenue_model": data.get("revenue_model"),
        "customer_evidence": {
            "interviews": data.get("customer_interviews"),
            "has_interviews": data.get("has_customer_interviews"),
            "problem_evidence": data.get("problem_evidence"),
            "willingness_to_pay": data.get("willingness_to_pay"),
            "prototype_tested": data.get("prototype_tested"),
            "notes": data.get("demand_evidence"),
        },
        "local_assessment": {"score": report.get("score"), "classification": report.get("classification"), "factor_scores": report.get("factor_scores")},
    }
    system_prompt = (
        "You are assisting with a preliminary startup idea review. Return ONLY valid JSON with keys: "
        "summary (string), recommendations (array of 3 to 5 strings), and swot (object with arrays strengths, weaknesses, opportunities, threats). "
        "Never invent or state verified market size, competitor facts, survey results, regulations, customer demand, or research not supplied. "
        "Label inferred opportunities as hypotheses to test. Be specific to the submitted idea. The numeric score and classification must not change."
    )
    payload = {
        "model": model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload_context, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
    }
    request = Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        content = response_data["choices"][0]["message"]["content"]
        enhanced = json.loads(content)
        result = dict(report)
        if isinstance(enhanced.get("summary"), str) and enhanced["summary"].strip():
            result["summary"] = enhanced["summary"].strip()[:1600]
        if isinstance(enhanced.get("recommendations"), list):
            recs = [str(x).strip()[:500] for x in enhanced["recommendations"] if str(x).strip()]
            if 3 <= len(recs) <= 5:
                result["recommendations"] = recs
        if isinstance(enhanced.get("swot"), dict):
            swot = {}
            for key in ("strengths", "weaknesses", "opportunities", "threats"):
                vals = enhanced["swot"].get(key, [])
                swot[key] = [str(x).strip()[:400] for x in vals if str(x).strip()][:4] if isinstance(vals, list) else report["swot"][key]
            if all(swot.values()):
                result["swot"] = swot
        result["assessment_method"] = "Local scoring with optional AI-assisted narrative (not independently verified)"
        return result
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError, IndexError, OSError):
        # The local engine always remains usable if the external API fails.
        return report
