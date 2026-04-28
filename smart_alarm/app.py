from flask import Flask, render_template, request, redirect, session
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Required for session-based history (change this in production!)
app.secret_key = os.environ.get("SECRET_KEY", "smart-alarm-secret-2024")

MAX_HISTORY = 20   # per-user cap


# ── Sleep Prediction Logic ──────────────────────────────────────
def calculate_wake_times(sleep_time):
    results = []
    for cycles in [4, 5, 6]:
        wake_time = sleep_time + timedelta(minutes=90 * cycles)
        quality   = {6: "Excellent 😍", 5: "Good 🙂", 4: "Average 😐"}[cycles]
        percent   = int((cycles / 6) * 100)
        results.append({
            "time":    wake_time.strftime("%I:%M %p"),
            "quality": quality,
            "percent": percent,
        })
    return results


# ── Home Route ──────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def home():
    # Each user gets their own history list stored in their session cookie
    if "history" not in session:
        session["history"] = []

    wake_times = None

    if request.method == "POST":
        sleep_input = request.form.get("sleep_time", "").strip()
        if not sleep_input:
            return redirect("/")

        try:
            now        = datetime.now()
            sleep_time = datetime.combine(now.date(),
                         datetime.strptime(sleep_input, "%H:%M").time())

            # Push to tomorrow if the time has already passed today
            if sleep_time < now:
                sleep_time += timedelta(days=1)

        except ValueError:
            return redirect("/")

        wake_times = calculate_wake_times(sleep_time)

        # Prepend so newest entry is first (reversed list, no need to reverse in template)
        history = session["history"]
        history.insert(0, {"input": sleep_input, "result": wake_times})

        # Trim to cap
        session["history"] = history[:MAX_HISTORY]

        # Mark session as modified so Flask writes the cookie
        session.modified = True

    return render_template("index.html",
                           wake_times=wake_times,
                           history=session["history"])


# ── Clear History ───────────────────────────────────────────────
@app.route("/clear")
def clear():
    session["history"] = []
    session.modified   = True
    return redirect("/")


# ── Service-Worker (must be served from root scope) ─────────────
@app.route("/service-worker.js")
def service_worker():
    from flask import send_from_directory, Response
    sw_path = os.path.join(app.root_path, "static")
    resp = app.send_static_file("service-worker.js")
    # SW must be served with this header so it controls the full origin
    resp.headers["Service-Worker-Allowed"] = "/"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)