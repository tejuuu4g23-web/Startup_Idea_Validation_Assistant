# AI-Based Startup Idea Validation Assistant

**VentureLens** is a local-first academic web application for structuring an early-stage startup idea assessment. It collects founder inputs, calculates an explainable weighted score, highlights assumptions, creates a SWOT review, suggests a small MVP, and provides a 30-day market validation roadmap.

> **Important limitation:** This is a preliminary assessment tool. Scores are based on self-reported founder ratings and project-defined weights. They are not a probability of startup success, verified market research, or proof of product-market fit.

## Abstract and introduction

Startup idea validation is the process of testing whether a problem is worth solving, who experiences it, and whether the proposed solution can be delivered and supported by a viable business model. VentureLens provides a structured, local-first workflow for recording these assumptions and planning low-cost experiments.

## Problem statement

Founders can mistake enthusiasm or informal feedback for evidence of customer demand. They may start building before understanding target customers, alternatives, feasibility, and willingness to pay. This project organises these questions into an explainable assessment and an actionable report.

## Project objectives

- Make common startup assumptions explicit.
- Calculate a reproducible score from founder-supplied ratings and disclosed weights.
- Identify relative strengths, weak factors, and missing evidence.
- Suggest an MVP and practical market experiments.
- Preserve evaluations locally so a founder can return to and compare reports.

## Proposed system and architecture

The browser submits the evaluation form to Flask. Flask validates the fields and passes them to the local assessment engine. The engine calculates factor scores, classification, recommendations, SWOT findings, an MVP outline, and a roadmap. SQLite stores the submitted context and report as a persistent evaluation record. The dashboard queries SQLite and therefore remains empty until a report is saved.

```text
Browser form → Flask input validation → Validation engine
                                      ↓
Dashboard ← SQLite ← Save assessment report
     ↓
Saved reports / Printable detail report
```

## Features

- Responsive dashboard with KPIs calculated only from saved evaluations.
- Fresh-install dashboard has zero metrics and no preloaded or fabricated reports.
- Guided startup idea form covering problem, solution, target customers, value proposition, revenue model, resources, and evidence.
- Weighted explainable scoring across eight factors.
- Context-driven recommendations and missing-evidence checklist.
- SWOT analysis that flags opportunities as hypotheses to test.
- MVP outline with essential features, items to postpone, acquisition approach, and metrics.
- Four-phase, illustrative 30-day validation roadmap.
- SQLite report persistence, classification filters, report detail, delete action, and browser print / Save as PDF.
- Optional OpenAI-compatible narrative enhancement; the app works without an API key and falls back to the local engine if an API call fails.
- CSRF checks for form writes and delete actions.

## Technology stack

- Python 3.11+ (other recent compatible versions may also work)
- Flask
- SQLite (`sqlite3` from the Python standard library)
- HTML5, CSS3, JavaScript
- Optional AI enhancement through an OpenAI-compatible Chat Completions endpoint using the Python standard library

## Project structure

```text
Startup_Idea_Validation_Assistant/
├── app.py
├── validation_engine.py
├── database.py
├── ai_enhancer.py
├── requirements.txt
├── README.md
├── .env.example
├── run_project.bat
├── database/
│   └── .gitkeep
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── validate.html
│   ├── reports.html
│   ├── report_detail.html
│   ├── about.html
│   └── 404.html
├── static/
│   ├── css/style.css
│   └── js/app.js
└── tests/
    ├── test_validation_engine.py
    ├── test_database.py
    └── test_app.py
```

The SQLite database file is created automatically at `database/startup_validation.db` during app startup. It is intentionally not shipped with sample reports, so a fresh installation starts empty.

## Scoring methodology

Each factor is rated from 1 to 5. A rating is mapped to a normalized factor score:

```text
Factor score = ((rating - 1) / 4) * 100
Weighted contribution = Factor score * factor weight / 100
Overall score = sum of weighted contributions
```

| Factor | Weight |
|---|---:|
| Problem severity | 15% |
| Target customer clarity | 15% |
| Market demand evidence | 20% |
| Product differentiation | 15% |
| Revenue model clarity | 10% |
| Feasibility and resources | 10% |
| Understanding of competition | 10% |
| Scalability potential | 5% |
| **Total** | **100%** |

Project-defined classifications:

- **75–100 — Promising:** proceed with structured market experiments.
- **50–74.9 — Needs Further Validation:** address weaker assumptions.
- **0–49.9 — High Uncertainty:** revisit the problem, customer, and evidence.

These thresholds are heuristic design choices for the academic project, not experimentally validated business rules. Since they are based on founder-provided ratings, interview notes and observed customer actions should be collected separately.

## Run on Windows

### Simple method

1. Extract the project ZIP.
2. Install Python 3.11 or newer if not installed. During setup, enable **Add Python to PATH**.
3. Double-click `run_project.bat`.
4. The script creates `.venv`, installs Flask, and starts the server.
5. Open <http://127.0.0.1:5000>.
6. Keep the terminal window open while using the application. Press `Ctrl+C` to stop the server.

The first run requires internet access to install the Flask package. After installation, the core scoring/report workflow runs locally without an AI API key.

### Manual Command Prompt method

Open Command Prompt in the extracted project folder and execute:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Then visit `http://127.0.0.1:5000` in your browser.

### Optional AI-assisted narrative enhancement

The local scoring/recommendation engine is the default and needs no key. To use the optional OpenAI-compatible API:

1. Copy `.env.example` to `.env`.
2. Set `AI_ENHANCEMENT_ENABLED=true` and provide your own `OPENAI_API_KEY`.
3. Optionally set `OPENAI_MODEL` and `OPENAI_BASE_URL` to values supported by your provider.
4. Restart the app.

The application reads those values from the environment or `.env` file. Never commit or share `.env`. An enabled request sends submitted idea text and assessment context to the configured provider. If the API is unavailable or returns malformed data, the local report is kept. AI-assisted narrative may still be inaccurate and should be reviewed. Do not enter confidential business information unless you are comfortable sending it to the configured provider.

## Screenshots

Capture screenshots from the running application rather than using mockups as evidence. Recommended screenshots for a college submission:

1. Dashboard on a fresh database showing zero metrics and the empty state.
2. The idea evaluation form showing business details and the factor rating section.
3. A completed report showing the validation score and factor breakdown.
4. The SWOT and MVP recommendations section.
5. The saved reports page after at least one evaluation has been submitted.

On Windows, use `Win + Shift + S` to capture the relevant application area. If an actual screenshot has not been captured, do not claim one is included in the project.

## Module descriptions

- **Dashboard:** saved report KPIs, readiness distribution, and recently evaluated ideas.
- **Idea intake:** startup context, business model, evidence, and eight weighted ratings.
- **Assessment engine:** deterministic score calculation and context-sensitive rule-based findings.
- **SWOT and recommendations:** preliminary strengths, weaknesses, hypotheses to validate, and threats or unknowns.
- **MVP and roadmap:** the first essential workflow, items to postpone, initial metrics, and an illustrative 30-day test sequence.
- **Reports:** persisted reports, classification filter, deletion, and browser print / Save as PDF.

## Existing-system limitations

This version does not claim to run independent market research, source-verified competitor discovery, customer surveys, or historic outcome modelling. It addresses the coursework problem as an explainable preliminary assessment. Future versions could add sourced research and actual validation evidence tracking.

## Suggested demo flow

1. Open the dashboard and point out that all metrics are zero because there are no saved reports.
2. Click **Validate an idea** and enter your idea, intended customers, business model, and evidence.
3. Choose ratings from 1 to 5 and submit the form.
4. Review the score, factor breakdown, strengths, weaknesses, SWOT, recommendations, MVP, and roadmap.
5. Return to the dashboard and show how its counts now reflect the saved evaluation.
6. Open **Saved reports**, revisit the report, then use **Print / Save PDF**.
7. Demonstrate the delete action only if you are comfortable removing the test report.

For academic honesty, identify any idea entered during the demo as a sample/demo submission and do not claim that assessment suggestions are verified market research.

## Testing

Run the standard-library tests from the project folder:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The scoring and database tests use only Python's standard library. Flask route tests run when Flask is installed. Review the terminal output to see which tests actually executed; do not report skipped tests as passed.

## Database design

The `evaluations` table stores the original idea context, evidence answers, ratings JSON, report JSON, score, classification, and creation timestamp. Dashboard cards and recent reports are computed from these stored records. Deleting a report removes the saved record and therefore updates future dashboard calculations.

## Limitations

- Scores reflect user-entered ratings and are not calibrated against historical startup outcomes.
- Competitor information is based on what the founder entered; the system does not independently verify competitors or market size.
- Local recommendations are explainable heuristics. Optional LLM-generated narrative is not independently verified.
- The printable report uses the browser's print dialog; the user can choose “Save as PDF”.
- The local development server is intended for coursework and should not be exposed directly to the public internet.

## Future scope

- Research with cited sources and verified competitor comparison.
- Attachments for interview notes and evidence.
- Version comparisons to track score changes as assumptions are tested.
- Team collaboration, authentication, and export features for a production deployment.

## Conclusion

VentureLens provides a useful first-pass workflow for documenting startup assumptions and planning low-cost tests. The score makes assumptions visible; real decisions should be driven by evidence from customers and experiments.
