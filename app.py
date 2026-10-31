"""Flask web application for the Startup Idea Validation Assistant."""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from ai_enhancer import enhance_report_if_configured
from database import DEFAULT_DB_PATH, dashboard_metrics, delete_evaluation, get_evaluation, init_db, list_evaluations, save_evaluation
from validation_engine import FACTOR_HELP, FACTOR_LABELS, WEIGHTS, evaluate_idea, validate_inputs

BASE_DIR = Path(__file__).resolve().parent


def _load_local_env() -> None:
    """Load simple KEY=VALUE entries from .env without a third-party dependency."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"\''))
    except OSError:
        return


_load_local_env()


def _form_payload(form: Any) -> dict[str, Any]:
    ratings = {key: form.get(key, "") for key in WEIGHTS}
    return {
        "idea_name": form.get("idea_name", "").strip(),
        "industry": form.get("industry", "").strip(),
        "description": form.get("description", "").strip(),
        "problem": form.get("problem", "").strip(),
        "solution": form.get("solution", "").strip(),
        "target_customers": form.get("target_customers", "").strip(),
        "geographic_market": form.get("geographic_market", "").strip(),
        "uvp": form.get("uvp", "").strip(),
        "competitors": form.get("competitors", "").strip(),
        "revenue_model": form.get("revenue_model", "").strip(),
        "initial_budget": form.get("initial_budget", "0").strip(),
        "skills_resources": form.get("skills_resources", "").strip(),
        "has_customer_interviews": form.get("has_customer_interviews", "unknown"),
        "customer_interviews": form.get("customer_interviews", "0").strip(),
        "problem_evidence": form.get("problem_evidence", "unknown"),
        "willingness_to_pay": form.get("willingness_to_pay", "unknown"),
        "prototype_tested": form.get("prototype_tested", "unknown"),
        "demand_evidence": form.get("demand_evidence", "").strip(),
        "ratings": ratings,
    }


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32),
        DATABASE=str(DEFAULT_DB_PATH),
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    init_db(app.config["DATABASE"])

    @app.context_processor
    def inject_layout_globals() -> dict[str, Any]:
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"], "current_year": 2026}

    def csrf_is_valid() -> bool:
        sent = request.form.get("csrf_token", "")
        expected = session.get("csrf_token", "")
        return bool(sent and expected and secrets.compare_digest(sent, expected))

    @app.get("/")
    def dashboard():
        metrics = dashboard_metrics(app.config["DATABASE"])
        recent = list_evaluations(app.config["DATABASE"])[:5]
        total = max(metrics["total"], 1)
        distribution = [
            {"label": label, "count": count, "percent": round(count * 100 / total), "class_name": css_class}
            for label, count, css_class in [
                ("Promising", metrics["distribution"]["Promising"], "promising"),
                ("Needs Further Validation", metrics["distribution"]["Needs Further Validation"], "needs"),
                ("High Uncertainty", metrics["distribution"]["High Uncertainty"], "uncertain"),
            ]
        ]
        return render_template("dashboard.html", metrics=metrics, recent=recent, distribution=distribution)

    @app.route("/validate", methods=["GET", "POST"])
    def validate():
        form_data: dict[str, Any] = {}
        form_errors: list[str] = []
        if request.method == "POST":
            if not csrf_is_valid():
                flash("Your form session expired. Please try submitting the form again.", "error")
                return redirect(url_for("validate"))
            form_data = _form_payload(request.form)
            form_errors = validate_inputs(form_data)
            if form_errors:
                return render_template(
                    "validate.html", form_data=form_data, form_errors=form_errors,
                    factor_labels=FACTOR_LABELS, factor_help=FACTOR_HELP, weights=WEIGHTS,
                ), 400
            try:
                report = evaluate_idea(form_data)
                report = enhance_report_if_configured(form_data, report)
                new_id = save_evaluation(form_data, report, app.config["DATABASE"])
            except (ValueError, TypeError) as exc:
                flash(f"The idea could not be evaluated: {exc}", "error")
                return render_template(
                    "validate.html", form_data=form_data, form_errors=[str(exc)],
                    factor_labels=FACTOR_LABELS, factor_help=FACTOR_HELP, weights=WEIGHTS,
                ), 400
            flash("Your startup idea has been evaluated and saved.", "success")
            return redirect(url_for("report_detail", report_id=new_id))

        return render_template(
            "validate.html", form_data=form_data, form_errors=form_errors,
            factor_labels=FACTOR_LABELS, factor_help=FACTOR_HELP, weights=WEIGHTS,
        )

    @app.get("/reports")
    def reports():
        selected = request.args.get("classification", "").strip()
        allowed = {"Promising", "Needs Further Validation", "High Uncertainty"}
        rows = list_evaluations(app.config["DATABASE"])
        if selected in allowed:
            rows = [row for row in rows if row["classification"] == selected]
        else:
            selected = ""
        return render_template("reports.html", reports=rows, selected=selected, classifications=sorted(allowed))

    @app.get("/report/<int:report_id>")
    def report_detail(report_id: int):
        evaluation = get_evaluation(report_id, app.config["DATABASE"])
        if evaluation is None:
            abort(404)
        return render_template("report_detail.html", evaluation=evaluation, report=evaluation["report"])

    @app.post("/report/<int:report_id>/delete")
    def report_delete(report_id: int):
        if not csrf_is_valid():
            flash("Your form session expired. Please try again.", "error")
            return redirect(url_for("reports"))
        deleted = delete_evaluation(report_id, app.config["DATABASE"])
        if deleted:
            flash("Evaluation report deleted.", "success")
        else:
            flash("That report was not found.", "error")
        return redirect(url_for("reports"))

    @app.get("/about")
    def about():
        return render_template("about.html", weights=WEIGHTS, factor_labels=FACTOR_LABELS)

    @app.errorhandler(404)
    def not_found(_error: Any):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(_error: Any):
        flash("The submitted form was too large. Please shorten the text fields and try again.", "error")
        return redirect(url_for("validate")), 413

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=debug)
