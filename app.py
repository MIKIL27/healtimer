import os
import uuid
from datetime import date, timedelta

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


APP_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(APP_DIR, "templates"),
)

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
    """Parse a stored ISO date."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def get_entry(entry_id):
    """Find an active injury entry in the signed-cookie session."""
    for entry in session.get("active_injuries", []):
        if entry.get("entry_id") != entry_id:
            continue

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
    progress = min(100, max(0, elapsed_days / max_days * 100))
    earliest_marker = min(100, min_days / max_days * 100)

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
    """Only redirect to a local path supplied by the app."""
    if candidate and candidate.startswith("/") and not candidate.startswith("//"):
        return candidate

    return url_for(default_endpoint)


def simple_error_page(title, message, status_code):
    """Render an error page without depending on base.html."""
    page = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1, viewport-fit=cover">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
        <meta name="theme-color" content="#f5f6f8">
        <title>{{ title }} · HealTimer</title>
        <style>
          * { box-sizing: border-box; }
          body {
            margin: 0;
            padding: 0 18px calc(90px + env(safe-area-inset-bottom));
            background: #f5f6f8;
            color: #18202b;
            font: 17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }
          header {
            padding: calc(env(safe-area-inset-top) + 14px) 0 14px;
            background: #fff;
            border-bottom: 2px solid #e17a32;
          }
          .header-inner, main, nav > div {
            width: min(100%, 620px);
            margin: 0 auto;
          }
          .header-inner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            flex-wrap: wrap;
          }
          .brand { color: #18202b; font-weight: 800; text-decoration: none; }
          form.demo { display: flex; gap: 5px; flex-wrap: wrap; }
          form.demo button {
            min-height: 36px;
            padding: 6px 9px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: #fff;
            font: inherit;
            font-size: 12px;
          }
          .badge {
            width: fit-content;
            margin: 10px auto 0;
            padding: 6px 10px;
            border-radius: 999px;
            background: #fff0e3;
            font-size: 13px;
            font-weight: 700;
          }
          main { padding-top: 15vh; }
          section {
            padding: 24px;
            border-radius: 18px;
            background: #fff;
            box-shadow: 0 8px 28px rgba(31, 43, 60, .08);
          }
          a.home {
            display: inline-flex;
            min-height: 48px;
            align-items: center;
            margin-top: 10px;
            padding: 12px 17px;
            border-radius: 14px;
            background: #e17a32;
            color: #fff;
            font-weight: 750;
            text-decoration: none;
          }
          nav {
            position: fixed;
            right: 0;
            bottom: 0;
            left: 0;
            padding: 8px 16px calc(8px + env(safe-area-inset-bottom));
            background: #fff;
          }
          nav > div { display: flex; justify-content: space-around; }
          nav a { padding: 12px; color: #697386; text-decoration: none; }
          @media (prefers-color-scheme: dark) {
            body { background: #101216; color: #f3f5f8; }
            header, section, nav, form.demo button { background: #1c2027; }
            .brand { color: #f3f5f8; }
            section { box-shadow: 0 8px 28px rgba(0, 0, 0, .22); }
          }
        </style>
      </head>
      <body>
        <header>
          <div class="header-inner">
            <a class="brand" href="{{ url_for('home') }}">HealTimer</a>
            <form class="demo" method="post" action="{{ url_for('set_demo_offset') }}">
              <input type="hidden" name="next" value="{{ request.path }}">
              <button type="submit" name="action" value="plus_one">+1 day</button>
              <button type="submit" name="action" value="plus_seven">+7 days</button>
              <button type="submit" name="action" value="plus_thirty">+30</button>
              <button type="submit" name="action" value="reset">Reset</button>
            </form>
          </div>
          {% set demo_offset = session.get('demo_offset_days', 0)|int %}
          {% if demo_offset != 0 %}
            <div class="badge">Demo mode: +{{ demo_offset }} days</div>
          {% endif %}
        </header>
        <main>
          <section>
            <h1>{{ title }}</h1>
            <p>{{ message }}</p>
            <a class="home" href="{{ url_for('home') }}">Go to Home</a>
          </section>
        </main>
        <nav aria-label="Main navigation">
          <div>
            <a href="{{ url_for('home') }}">Home</a>
            <a href="{{ url_for('catalogue') }}">Catalogue</a>
            <a href="{{ url_for('notifications') }}">Notifications</a>
          </div>
        </nav>
      </body>
    </html>
    """

    return render_template_string(
        page,
        title=title,
        message=message,
    ), status_code


@app.get("/")
def home():
    injury_views = []

    for entry in session.get("active_injuries", []):
        injury = INJURIES.get(entry.get("injury_id"))
        if not injury or entry.get("severity") not in injury["severities"]:
            continue
        injury_views.append(build_entry_view(entry, injury))

    header_stage = (
        injury_views[0]["stage"]["css_class"]
        if injury_views
        else "stage-2"
    )

    return render_template(
        "home.html",
        injuries=injury_views,
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

    # Include each dictionary key as an id for the category template links.
    injuries = [
        {"id": injury_id, **injury}
        for injury_id, injury in INJURIES.items()
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
            flash(
                "That severity was not recognized, so Mild was selected.",
                "error",
            )

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
            flash(
                "That severity was not recognized, so Mild is shown.",
                "error",
            )

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
        current_stage_index = view["stage"]["index"]
        next_stage = dict(STAGES[current_stage_index + 1])
        threshold_percent = [25, 50, 80][current_stage_index]
        next_stage_day = round(view["max_days"] * threshold_percent / 100)
        days_until = max(0, next_stage_day - view["elapsed_days"])

        if days_until == 0:
            next_stage["when"] = "about today"
        else:
            unit = "day" if days_until == 1 else "days"
            next_stage["when"] = f"in about {days_until} {unit}"

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
    }
    action = request.form.get("action")

    if action == "reset":
        session["demo_offset_days"] = 0
    elif action in actions:
        try:
            current_offset = int(session.get("demo_offset_days", 0))
        except (TypeError, ValueError):
            current_offset = 0

        session["demo_offset_days"] = max(
            -36500,
            min(36500, current_offset + actions[action]),
        )

    return redirect(safe_return_path(request.form.get("next")))


@app.post("/disclaimer/accept")
def accept_disclaimer():
    session["disclaimer_accepted"] = True
    return redirect(safe_return_path(request.form.get("next")))


@app.errorhandler(404)
def not_found(_error):
    return simple_error_page(
        "Page not found",
        "That page may have moved, or the link may be out of date.",
        404,
    )


@app.errorhandler(500)
def server_error(_error):
    return simple_error_page(
        "Something went wrong",
        "We couldn’t load this page. Please try again in a moment.",
        500,
    )


if __name__ == "__main__":
    # Local testing only. Production deployments should use debug=False.
    app.run(debug=False)
