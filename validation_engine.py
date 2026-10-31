"""Explainable, local-first startup idea assessment engine.

Scores are heuristic self-assessments, not a probability of business success.
"""
from __future__ import annotations

from typing import Any

WEIGHTS = {
    "problem_severity": 15,
    "target_customer_clarity": 15,
    "market_demand_evidence": 20,
    "product_differentiation": 15,
    "revenue_model_clarity": 10,
    "feasibility_resources": 10,
    "competition_understanding": 10,
    "scalability_potential": 5,
}

FACTOR_LABELS = {
    "problem_severity": "Problem severity",
    "target_customer_clarity": "Target customer clarity",
    "market_demand_evidence": "Market demand evidence",
    "product_differentiation": "Product differentiation",
    "revenue_model_clarity": "Revenue model clarity",
    "feasibility_resources": "Feasibility and resources",
    "competition_understanding": "Understanding of competition",
    "scalability_potential": "Scalability potential",
}

FACTOR_HELP = {
    "problem_severity": "How painful, frequent, or costly is the problem for the target customer?",
    "target_customer_clarity": "How specifically can you describe who will use or buy this solution?",
    "market_demand_evidence": "How much direct evidence supports that customers need or want this solution?",
    "product_differentiation": "How clearly does the proposed solution differ from alternatives?",
    "revenue_model_clarity": "Do you understand who pays, what they pay for, and how often?",
    "feasibility_resources": "Can your current skills, resources, time, and budget deliver a small first version?",
    "competition_understanding": "Have you identified existing products, substitutes, or manual workarounds?",
    "scalability_potential": "Could the solution serve more customers without costs rising at the same rate?",
}

VALID_YES_NO_UNKNOWN = {"yes", "no", "unknown"}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _list_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [_clean_text(item) for item in value if _clean_text(item)]
    return []


def validate_inputs(data: dict[str, Any]) -> list[str]:
    """Return validation errors; an empty list means the data is valid."""
    errors: list[str] = []
    required = {
        "idea_name": "Startup idea name",
        "industry": "Industry",
        "description": "Idea description",
        "problem": "Problem being solved",
        "solution": "Proposed solution",
        "target_customers": "Target customers",
        "geographic_market": "Geographic market",
        "uvp": "Unique value proposition",
        "revenue_model": "Revenue model",
        "skills_resources": "Available skills and resources",
    }
    for key, label in required.items():
        if not _clean_text(data.get(key)):
            errors.append(f"{label} is required.")
        elif len(_clean_text(data.get(key))) > 3000:
            errors.append(f"{label} must be 3,000 characters or fewer.")

    if len(_clean_text(data.get("idea_name"))) > 120:
        errors.append("Startup idea name must be 120 characters or fewer.")
    if len(_clean_text(data.get("industry"))) > 100:
        errors.append("Industry must be 100 characters or fewer.")
    if len(_clean_text(data.get("description"))) > 1500:
        errors.append("Idea description must be 1,500 characters or fewer.")

    try:
        budget = float(data.get("initial_budget", 0))
        if budget < 0 or budget > 1_000_000_000_000:
            errors.append("Initial budget must be between ₹0 and ₹1,000,000,000,000.")
    except (TypeError, ValueError):
        errors.append("Initial budget must be a valid number.")

    try:
        interviews = int(data.get("customer_interviews", 0))
        if interviews < 0 or interviews > 1_000_000:
            errors.append("Interview/survey count must be between 0 and 1,000,000.")
    except (TypeError, ValueError):
        errors.append("Interview/survey count must be a whole number.")

    for key, label in {
        "has_customer_interviews": "Customer interviews",
        "problem_evidence": "Evidence of the problem",
        "willingness_to_pay": "Willingness to pay",
        "prototype_tested": "Prototype testing",
    }.items():
        if str(data.get(key, "unknown")).lower() not in VALID_YES_NO_UNKNOWN:
            errors.append(f"{label} must be Yes, No, or Not sure.")

    raw_ratings = data.get("ratings", {})
    if not isinstance(raw_ratings, dict):
        errors.append("Assessment ratings are missing or invalid.")
        raw_ratings = {}
    for key, label in FACTOR_LABELS.items():
        try:
            rating = int(raw_ratings.get(key, ""))
            if rating not in range(1, 6):
                errors.append(f"{label} must be rated from 1 to 5.")
        except (TypeError, ValueError):
            errors.append(f"{label} must be rated from 1 to 5.")

    return errors


def classify_score(score: float) -> str:
    if score >= 75:
        return "Promising"
    if score >= 50:
        return "Needs Further Validation"
    return "High Uncertainty"


def _make_recommendations(data: dict[str, Any], factor_scores: dict[str, dict[str, Any]]) -> list[str]:
    recommendations: list[str] = []
    priorities = sorted(factor_scores.items(), key=lambda item: item[1]["score"])
    low_recommendations = {
        "problem_severity": "Interview target customers about the frequency, impact, and current cost of the problem before committing to a build.",
        "target_customer_clarity": "Narrow the audience to one initial customer segment and describe its role, context, and main need in one sentence.",
        "market_demand_evidence": "Run 8–12 problem interviews and one low-cost demand test; record behaviour and evidence rather than relying only on opinions.",
        "product_differentiation": "Compare at least three direct or indirect alternatives and test whether customers value your stated difference.",
        "revenue_model_clarity": "Test a specific price or pricing package with potential buyers and identify who approves and pays.",
        "feasibility_resources": "Reduce the first release to one core workflow and confirm the skills, time, and budget needed to deliver it.",
        "competition_understanding": "Research direct competitors, indirect substitutes, and manual workarounds; do not assume the market has no competition.",
        "scalability_potential": "Test a repeatable way to reach customers and estimate how delivery and support costs change as usage grows.",
    }
    for key, details in priorities:
        if details["score"] < 60 and len(recommendations) < 4:
            recommendations.append(low_recommendations[key])

    interviews = int(data.get("customer_interviews", 0) or 0)
    if interviews < 5 and len(recommendations) < 5:
        recommendations.append("Build an evidence log from at least five conversations with people in the target customer group; note repeated problems and objections.")
    if data.get("willingness_to_pay") != "yes" and len(recommendations) < 5:
        recommendations.append("Validate willingness to pay with a concrete offer, price range, pilot, or preorder test where appropriate.")
    if data.get("prototype_tested") != "yes" and len(recommendations) < 5:
        recommendations.append("Create a clickable mock-up, landing page, or manual concierge prototype and observe how target users respond.")
    if not recommendations:
        recommendations = [
            "Test the riskiest business assumption with a small, measurable customer experiment.",
            "Compare your value proposition with the alternatives customers already use.",
            "Define one measurable go/no-go threshold before spending more time or money.",
        ]
    return recommendations[:5]


def _swot(data: dict[str, Any], factor_scores: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    strong = [
        f"{details['label']} is a relative strength based on your self-assessment ({details['score']:.0f}/100)."
        for details in factor_scores.values() if details["score"] >= 75
    ][:3]
    if data.get("uvp"):
        strong.append("A proposed value proposition has been articulated and can now be tested with target customers.")
    if not strong:
        strong.append("The problem and proposed solution have been documented, providing a starting point for structured validation.")

    weak = [
        f"{details['label']} needs attention (self-assessed score: {details['score']:.0f}/100)."
        for details in sorted(factor_scores.values(), key=lambda item: item["score"]) if details["score"] < 60
    ][:3]
    if data.get("has_customer_interviews") != "yes" or int(data.get("customer_interviews", 0) or 0) < 5:
        weak.append("Customer discovery evidence is limited or not yet established in the submitted information.")
    if not weak:
        weak.append("The assessment relies on founder inputs; independent customer evidence should still be collected.")

    target = _clean_text(data.get("target_customers")) or "the stated target customer"
    problem = _clean_text(data.get("problem")) or "the stated problem"
    opportunities = [
        f"Hypothesis to test: {target} may value a better way to address {problem.rstrip('.')}.",
        "A small prototype, pilot, or landing-page experiment could reveal what users value before a larger investment.",
    ]
    if data.get("geographic_market"):
        opportunities.append(f"Test the idea with a clearly defined initial geography ({_clean_text(data['geographic_market'])}) before expanding.")

    threats = []
    if _clean_text(data.get("competitors")):
        threats.append("The alternatives listed by the founder may already meet some customer needs; compare them using customer-relevant criteria.")
    else:
        threats.append("The competitive landscape has not been described; direct, indirect, and manual alternatives remain an open question.")
    if float(data.get("initial_budget", 0) or 0) < 50000:
        threats.append("A limited initial budget may constrain testing and delivery; validate the lowest-cost path before building more features.")
    threats.append("Customer interest, willingness to pay, regulations, and acquisition costs have not been independently verified by this assessment.")

    return {
        "strengths": strong[:4],
        "weaknesses": weak[:4],
        "opportunities": opportunities[:4],
        "threats": threats[:4],
    }


def _mvp(data: dict[str, Any]) -> dict[str, Any]:
    problem = _clean_text(data.get("problem"))
    solution = _clean_text(data.get("solution"))
    target = _clean_text(data.get("target_customers"))
    uvp = _clean_text(data.get("uvp"))
    budget = float(data.get("initial_budget", 0) or 0)
    return {
        "core_problem": problem,
        "primary_customer": target,
        "goal": f"Test whether {target.lower()} will use or pay for a simple solution to: {problem[0].lower() + problem[1:] if problem else 'the stated problem'}",
        "essential_features": [
            f"One core workflow that delivers the first part of the proposed solution: {solution}",
            "A simple way for early users to get started and submit feedback or report friction.",
            "A basic way to record usage, enquiries, repeat use, or another agreed success metric.",
        ],
        "postpone": [
            "Advanced automation and integrations that early users have not requested.",
            "Large-scale infrastructure, complex analytics, and extensive customisation.",
            "Features outside the single customer problem being tested.",
        ],
        "prototype_approach": (
            "Start with a clickable mock-up, landing page, spreadsheet, or manual concierge service before commissioning custom software."
            if budget < 100000 else
            "Compare a clickable prototype with a small functional build; spend only on features needed to test the core assumption."
        ),
        "first_acquisition": f"Invite a small group of people who match {target} through relevant communities, direct outreach, or trusted introductions; explain the offer honestly.",
        "success_metrics": [
            "Number of qualified target-customer conversations completed.",
            "Share of interviewees who independently describe the same problem.",
            "Observed prototype use, repeat engagement, paid pilot interest, or another pre-defined commitment metric.",
        ],
        "value_proposition_to_test": uvp,
    }


def _roadmap(data: dict[str, Any]) -> list[dict[str, Any]]:
    target = _clean_text(data.get("target_customers"))
    return [
        {"phase": "1", "title": "Problem validation", "days": "Days 1–7", "goal": "Confirm that the problem is real and important for a specific audience.", "tasks": [f"Recruit 8–12 people who match {target}.", "Ask about their current workflow, recent examples, cost, and workarounds.", "Summarise repeated pain points and disconfirming feedback."]},
        {"phase": "2", "title": "Solution validation", "days": "Days 8–14", "goal": "Test whether the proposed approach solves the core problem.", "tasks": ["Create a simple mock-up or manual prototype.", "Ask target users to complete one realistic task.", "Record confusion, value moments, and requested changes."]},
        {"phase": "3", "title": "Demand validation", "days": "Days 15–23", "goal": "Test commitment and willingness to pay rather than interest alone.", "tasks": ["Show a clear offer and a specific price or pilot package.", "Measure qualified sign-ups, pilot commitments, or other relevant actions.", "Record objections and compare results with a threshold set in advance."]},
        {"phase": "4", "title": "Decision and iteration", "days": "Days 24–30", "goal": "Use evidence to decide the next small step.", "tasks": ["Summarise evidence, assumptions, costs, and unresolved risks.", "Compare results with the pre-defined success criteria.", "Decide to iterate, run another test, or reconsider the idea; do not treat this assessment score as proof of demand."]},
    ]


def evaluate_idea(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate validated input and return a report-ready dict."""
    errors = validate_inputs(data)
    if errors:
        raise ValueError(" ".join(errors))

    ratings = data["ratings"]
    factor_scores: dict[str, dict[str, Any]] = {}
    total = 0.0
    for key, weight in WEIGHTS.items():
        rating = int(ratings[key])
        # Map rating 1..5 onto 0..100, then apply the factor weight.
        normalized = ((rating - 1) / 4) * 100
        contribution = normalized * weight / 100
        total += contribution
        factor_scores[key] = {
            "key": key,
            "label": FACTOR_LABELS[key],
            "rating": rating,
            "weight": weight,
            "score": round(normalized, 1),
            "contribution": round(contribution, 2),
            "explanation": FACTOR_HELP[key],
        }

    score = round(max(0.0, min(100.0, total)), 1)
    classification = classify_score(score)
    ranked = sorted(factor_scores.values(), key=lambda item: item["score"], reverse=True)
    strengths = [f"{x['label']} is a relative strength ({x['score']:.0f}/100)." for x in ranked if x["score"] >= 75][:4]
    if not strengths:
        strengths = ["The idea has a documented problem and proposed solution; evidence gathering is the next step."]
    weaknesses = [f"{x['label']} is a priority to validate ({x['score']:.0f}/100)." for x in sorted(factor_scores.values(), key=lambda item: item["score"]) if x["score"] < 60][:4]
    if data.get("has_customer_interviews") != "yes" or int(data.get("customer_interviews", 0) or 0) < 5:
        weaknesses.append("Customer discovery is still limited; the score reflects founder self-assessment, not observed market behaviour.")
    if not weaknesses:
        weaknesses = ["No factor scored below 60/100, but independent customer evidence is still needed before a major investment."]

    if classification == "Promising":
        summary = "The submitted ratings indicate a comparatively strong starting point. Proceed with small, structured market experiments and verify the assumptions with customer behaviour before scaling."
    elif classification == "Needs Further Validation":
        summary = "The idea has some promising elements, but one or more assumptions need stronger evidence. Prioritise the lowest-scoring factors and run low-cost experiments before increasing investment."
    else:
        summary = "The current self-assessment indicates substantial uncertainty. Revisit the problem, target customer, and evidence, then test the riskiest assumptions before building a full product."

    missing: list[str] = []
    if data.get("has_customer_interviews") != "yes" or int(data.get("customer_interviews", 0) or 0) < 5:
        missing.append("At least five documented conversations with target customers.")
    if data.get("problem_evidence") != "yes":
        missing.append("Independent evidence that the target customers experience this problem.")
    if data.get("willingness_to_pay") != "yes":
        missing.append("Evidence of willingness to pay or commit to a relevant next step.")
    if data.get("prototype_tested") != "yes":
        missing.append("Feedback from a prototype, mock-up, pilot, or manual test.")
    if not _clean_text(data.get("demand_evidence")):
        missing.append("A written evidence log explaining what supports or contradicts demand.")
    if not _clean_text(data.get("competitors")):
        missing.append("A list of direct competitors, indirect substitutes, and current workarounds.")

    return {
        "score": score,
        "classification": classification,
        "summary": summary,
        "factor_scores": factor_scores,
        "strengths": strengths,
        "weaknesses": weaknesses[:4],
        "recommendations": _make_recommendations(data, factor_scores),
        "missing_evidence": missing,
        "swot": _swot(data, factor_scores),
        "mvp": _mvp(data),
        "roadmap": _roadmap(data),
        "scoring_note": "This project-defined score is a structured preliminary assessment based on founder-provided ratings. It is not a probability of success and does not replace customer research.",
        "assessment_method": "Local explainable scoring and rule-based recommendations",
    }
