import os
import uuid
from datetime import date, datetime, timedelta

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    render_template_string,
    request,
    session,
    url_for,
)

from data import ACTIVITIES, CATEGORIES, INJURIES, STAGES

app = Flask(__name__)

# Set SECRET_KEY in the deployment environment before publishing.
# This placeholder is for local testing only; change it before deployment.
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-placeholder-before-deployment",
)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


@app.before_request
def make_session_permanent():
    """Keep the signed-cookie session for up to one year."""
    session.permanent = True


def get_today():
    """Return today's date adjusted by the session's demo offset."""
    try:
        offset = int(session.get("demo_offset_days", 0))
    except (TypeError, ValueError):
        offset = 0
    return date.today() + timedelta(days=offset)


def get_stage(elapsed_days, max_days):
    """Find the shared healing stage based on elapsed/max healing time."""
    max_days = max(1, int(max_days))
    progress = max(0, elapsed_days) / max_days

    if progress < 0.25:
        stage_index = 0
    elif progress < 0.50:
        stage_index = 1
    elif progress < 0.80:
        stage_index = 2
    else:
        stage_index = 3

    stage = dict(STAGES[stage_index])
    stage["index"] = stage_index
    stage["css_class"] = f"stage-{stage_index + 1}"
    return stage


def remaining_range(elapsed_days, min_days, max_days):
    """Return the estimated remaining range and whether the window has passed."""
    min_left = max(0, min_days - elapsed_days)
    max_left = max(0, max_days - elapsed_days)
    return {
        "min_days": min_left,
        "max_days": max_left,
        "label": f"{min_left}–{max_left} days left",
        "passed": elapsed_days > max_days,
    }


def parse_start_date(value):
    """Parse a stored ISO date; malformed session data is treated as invalid."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def get_entry(entry_id):
    """Look up one active injury entry from the signed-cookie session."""
    for entry in session.get("active_injuries", []):
        if entry.get("entry_id") == entry_id:
            injury = INJURIES.get(entry.get("injury_id"))
            if injury and entry.get("severity") in injury["severities"]:
                return entry, injury
    abort(404)


def build_entry_view(entry, injury):
    """Add calculated values used by injury cards and detail pages."""
    severity_data = injury["severities"][entry["severity"]]
    start_date = parse_start_date(entry.get("start_date"))
    if start_date is None:
        abort(404)

    elapsed_days = max(0, (get_today() - start_date).days)
    min_days = severity_data["min_days"]
    max_days = severity_data["max_days"]
    stage = get_stage(elapsed_days, max_days)
    remaining = remaining_range(elapsed_days, min_days, max_days)
    progress = min(100, max(0, (elapsed_days / max_days) * 100))

    # The earliest marker represents min_days; the latest is max_days.
    earliest_marker = min(100, (min_days / max_days) * 100)

    return {
        "entry": entry,
        "injury": injury,
        "severity": entry["severity"].title(),
        "elapsed_days": elapsed_days,
        "min_days": min_days,
        "max_days": max_days,
        "stage": stage,
        "remaining": remaining,
        "progress_percent": round(progress, 1),
        "earliest_marker": round(earliest_marker, 1),
        "latest_marker": 100,
    }


def safe_return_path(candidate, default_endpoint="home"):
    """Only redirect to local paths supplied by the app."""
    if candidate and candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return url_for(default_endpoint)


@app.get("/")
def home():
    views = []
    for entry in session.get("active_injuries", []):
        injury = INJURIES.get(entry.get("injury_id"))
        if not injury or entry.get("severity") not in injury["severities"]:
            continue
        views.append(build_entry_view(entry, injury))

    header_stage = views[0]["stage"]["css_class"] if views else "stage-2"
    return render_template(
        "home.html",
        injuries=views,
        active_tab="home",
        stage_class=header_stage,
    )


@app.get("/catalogue")
def catalogue():
    return render_template(
        "catalogue.html",
        categories=CATEGORIES,
        active_tab="catalogue",
        stage_class="stage-2",
    )


@app.get("/category/<category_id>")
def category(category_id):
    category_data = CATEGORIES.get(category_id)
    if category_data is None:
        abort(404)

    injuries = [
        injury
        for injury in INJURIES.values()
        if injury["category_id"] == category_id
    ]
    return render_template(
        "category.html",
        category=category_data,
        injuries=injuries,
        active_tab="catalogue",
        stage_class="stage-2",
    )


@app.route("/injury/<injury_id>/start", methods=["GET", "POST"])
def injury_start(injury_id):
    injury = INJURIES.get(injury_id)
    if injury is None:
        abort(404)

    if request.method == "POST":
        severity = request.form.get("severity", "mild").lower()
        if severity not in injury["severities"]:
            severity = "mild"
            flash("That severity was not recognized, so Mild was selected.", "error")

        active_injuries = session.get("active_injuries", [])
        if len(active_injuries) >= 8:
            flash("You can track up to 8 injuries at a time.", "error")
            return redirect(url_for("home"))

        entry = {
            "entry_id": uuid.uuid4().hex[:12],
            "injury_id": injury_id,
            "severity": severity,
            "start_date": get_today().isoformat(),
        }
        active_injuries.append(entry)
        session["active_injuries"] = active_injuries
        return redirect(url_for("detail", entry_id=entry["entry_id"]))

    selected_severity = request.args.get("severity", "mild").lower()
    if selected_severity not in injury["severities"]:
        selected_severity = "mild"
        if request.args.get("severity"):
            flash("That severity was not recognized, so Mild is shown.", "error")

    preview = injury["severities"][selected_severity]
    return render_template(
        "injury_start.html",
        injury=injury,
        selected_severity=selected_severity,
        preview=preview,
        active_tab="catalogue",
        stage_class="stage-2",
    )


@app.get("/detail/<entry_id>")
def detail(entry_id):
    entry, injury = get_entry(entry_id)
    view = build_entry_view(entry, injury)

    category_data = CATEGORIES[injury["category_id"]]
    activity_matrix = category_data["activity_matrix"].copy()
    activity_matrix.update(injury.get("activity_overrides", {}))

    activities = [
        {
            "name": activity,
            "status": activity_matrix.get(activity, ["Limited"] * 4)[
                view["stage"]["index"]
            ],
        }
        for activity in ACTIVITIES
    ]

    next_stage = None
    if view["stage"]["index"] < len(STAGES) - 1:
        next_index = view["stage"]["index"] + 1
        next_stage = dict(STAGES[next_index])
        threshold_percent = [25, 50, 80][view["stage"]["index"]]
        next_stage_day = round(view["max_days"] * threshold_percent / 100)
        days_until = max(0, next_stage_day - view["elapsed_days"])
        next_stage["days_until"] = days_until
        next_stage["when"] = (
            "about today" if days_until == 0
            else f"in about {days_until} day" + ("" if days_until == 1 else "s")
        )

    return render_template(
        "detail.html",
        view=view,
        activities=activities,
        next_stage=next_stage,
        today_position=view["progress_percent"],
        active_tab="",
        stage_class=view["stage"]["css_class"],
    )


@app.post("/detail/<entry_id>/remove")
def remove_injury(entry_id):
    get_entry(entry_id)
    session["active_injuries"] = [
        entry
        for entry in session.get("active_injuries", [])
        if entry.get("entry_id") != entry_id
    ]
    flash("Injury removed from your list.", "success")
    return redirect(url_for("home"))


@app.get("/notifications")
def notifications():
    return render_template(
        "notifications.html",
        active_tab="notifications",
        stage_class="stage-2",
    )


@app.post("/demo/set")
def set_demo_offset():
    actions = {
        "plus_one": 1,
        "plus_seven": 7,
        "plus_thirty": 30,
        "reset": None,
    }
    action = request.form.get("action")

    if action in actions:
        if action == "reset":
            session["demo_offset_days"] = 0
        else:
            try:
                current = int(session.get("demo_offset_days", 0))
            except (TypeError, ValueError):
                current = 0
            session["demo_offset_days"] = max(
                -36500,
                min(36500, current + actions[action]),
            )

    return redirect(safe_return_path(request.form.get("next")))


@app.post("/disclaimer/accept")
def accept_disclaimer():
    session["disclaimer_accepted"] = True
    return redirect(safe_return_path(request.form.get("next")))


@app.errorhandler(404)
def not_found(_error):
    page = """
    {% extends "base.html" %}
    {% block content %}
      <section class="empty-state">
        <p class="eyebrow">Page not found</p>
        <h1>We couldn’t find that page.</h1>
        <p>It may have moved, or the link may be out of date.</p>
        <a class="button button-primary" href="{{ url_for('home') }}">Go to Home</a>
      </section>
    {% endblock %}
    """
    return render_template_string(
        page,
        active_tab="",
        stage_class="stage-2",
        title="Page not found",
    ), 404


@app.errorhandler(500)
def server_error(_error):
    page = """
    {% extends "base.html" %}
    {% block content %}
      <section class="empty-state">
        <p class="eyebrow">Something went wrong</p>
        <h1>We couldn’t load this page.</h1>
        <p>Please try again in a moment.</p>
        <a class="button button-primary" href="{{ url_for('home') }}">Go to Home</a>
      </section>
    {% endblock %}
    """
    return render_template_string(
        page,
        active_tab="",
        stage_class="stage-2",
        title="Something went wrong",
    ), 500


if __name__ == "__main__":
    # Local testing only. Production deployments should use debug=False.
    app.run(debug=False)
