import os
from datetime import date, timedelta
from urllib.parse import urlparse

from flask import Flask, abort, redirect, render_template, request, session, url_for

from data import CASES, CATEGORIES, SEVERITY, STATUS_NAMES

app = Flask(__name__, static_folder=None)
# Change this placeholder to a long, random secret before publishing.
app.secret_key = os.environ.get("SECRET_KEY", "change-this-placeholder-secret-key")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

STAGES = [
    {"name": "Rest", "number": 1, "class": "stage-1", "color": "#e45b63"},
    {"name": "Careful recovery", "number": 2, "class": "stage-2", "color": "#e4a336"},
    {"name": "Almost healed", "number": 3, "class": "stage-3", "color": "#43a879"},
]


@app.context_processor
def inject_severity():
    return {"SEVERITY": SEVERITY}


def get_today():
    """Return today's date adjusted by the session's demo offset."""
    offset = session.get("demo_offset", 0)
    if not isinstance(offset, int):
        offset = 0
    return date.today() + timedelta(days=offset)


def get_stage(elapsed_days, max_days):
    """Choose a recovery stage using elapsed days as a share of max_days."""
    progress = max(0, elapsed_days) / max_days
    if progress < 0.33:
        return STAGES[0]
    if progress < 0.66:
        return STAGES[1]
    return STAGES[2]


def remaining_range(case, elapsed_days):
    """Return the lower and upper healing estimates still remaining."""
    return (
        max(0, case["min_days"] - elapsed_days),
        max(0, case["max_days"] - elapsed_days),
    )


def get_started_cases():
    started = session.get("started_cases", {})
    return started if isinstance(started, dict) else {}


def safe_previous_page():
    """Redirect only to this app's own home, catalogue, or case page."""
    referrer = request.referrer
    if referrer:
        parsed = urlparse(referrer)
        if parsed.netloc == request.host and (
            parsed.path == url_for("home")
            or parsed.path == url_for("catalogue")
            or parsed.path.startswith("/case/")
        ):
            return parsed.path
    return url_for("home")


@app.get("/")
def home():
    cards = []
    for case_id, start_text in get_started_cases().items():
        case = CASES.get(case_id)
        if not case or case.get("no_countdown"):
            continue
        try:
            started = date.fromisoformat(start_text)
        except (TypeError, ValueError):
            continue
        elapsed = max(0, (get_today() - started).days)
        low, high = remaining_range(case, elapsed)
        progress = min(100, max(0, elapsed / case["max_days"] * 100))
        cards.append(
            {
                "id": case_id,
                "case": case,
                "elapsed": elapsed,
                "low": low,
                "high": high,
                "progress": progress,
                "stage": get_stage(elapsed, case["max_days"]),
            }
        )
    return render_template(
        "home.html",
        cards=cards,
        demo_offset=session.get("demo_offset", 0),
    )


@app.get("/catalogue")
def catalogue():
    grouped = [
        {
            "category": category,
            "cases": [
                (case_id, case)
                for case_id, case in CASES.items()
                if case["category_id"] == category["id"]
            ],
        }
        for category in CATEGORIES
    ]
    return render_template(
        "catalogue.html",
        groups=grouped,
        demo_offset=session.get("demo_offset", 0),
    )


@app.get("/case/<case_id>")
def case_page(case_id):
    case = CASES.get(case_id)
    if not case:
        abort(404)

    start_text = get_started_cases().get(case_id)
    started = None
    if start_text:
        try:
            started = date.fromisoformat(start_text)
        except (TypeError, ValueError):
            started = None

    details = None
    if started and not case.get("no_countdown"):
        elapsed = max(0, (get_today() - started).days)
        low, high = remaining_range(case, elapsed)
        stage = get_stage(elapsed, case["max_days"])
        today_position = min(100, max(0, elapsed / case["max_days"] * 100))
        activity_rows = [
            {
                "name": activity,
                "status_code": statuses[stage["number"] - 1],
                "status": STATUS_NAMES[statuses[stage["number"] - 1]],
            }
            for activity, *statuses in case["activities"]
        ]
        details = {
            "elapsed": elapsed,
            "low": low,
            "high": high,
            "stage": stage,
            "today_position": today_position,
            "activity_rows": activity_rows,
            "passed_window": elapsed > case["max_days"],
        }

    return render_template(
        "case.html",
        case=case,
        case_id=case_id,
        details=details,
        demo_offset=session.get("demo_offset", 0),
    )


@app.post("/case/<case_id>/start")
def start_case(case_id):
    case = CASES.get(case_id)
    if not case or case.get("no_countdown"):
        abort(404)
    started = get_started_cases().copy()
    started[case_id] = get_today().isoformat()
    session["started_cases"] = started
    return redirect(url_for("case_page", case_id=case_id))


@app.post("/case/<case_id>/stop")
def stop_case(case_id):
    if case_id not in CASES:
        abort(404)
    started = get_started_cases().copy()
    started.pop(case_id, None)
    session["started_cases"] = started
    return redirect(url_for("home"))


@app.post("/demo/<action>")
def demo(action):
    if action not in ("plus1", "plus7", "reset"):
        abort(404)
    if action == "reset":
        session["demo_offset"] = 0
    else:
        offset = session.get("demo_offset", 0)
        if not isinstance(offset, int):
            offset = 0
        session["demo_offset"] = offset + (1 if action == "plus1" else 7)
    return redirect(safe_previous_page())


@app.errorhandler(404)
def page_not_found(_error):
    return render_template("404.html", demo_offset=session.get("demo_offset", 0)), 404


@app.errorhandler(500)
def server_error(_error):
    return render_template("500.html", demo_offset=session.get("demo_offset", 0)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
