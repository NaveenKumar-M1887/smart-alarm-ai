from flask import Flask, render_template, request, redirect, jsonify
from datetime import datetime, timedelta


app = Flask(__name__)



# 📦 Memory Storage
history = []
MAX_HISTORY = 10


# 🧠 Sleep Prediction Logic
def calculate_wake_times(sleep_time):
    cycles = [4, 5, 6]
    results = []

    for c in cycles:
        total_sleep = 90 * c
        wake_time = sleep_time + timedelta(minutes=total_sleep)

        percent = int((c / 6) * 100)

        if c == 6:
            quality = "Excellent 😍"
        elif c == 5:
            quality = "Good 🙂"
        else:
            quality = "Average 😐"

        results.append({
            "time": wake_time.strftime("%I:%M %p"),
            "quality": quality,
            "percent": percent
        })

    return results





# 🌐 Home Route
@app.route("/", methods=["GET", "POST"])
def home():
    wake_times = None

    if request.method == "POST":
        sleep_input = request.form.get("sleep_time")

        if not sleep_input:
            return redirect("/")

        try:
            sleep_time = datetime.strptime(sleep_input, "%H:%M")

            # ⏱ Fix past time → next day
            now = datetime.now()
            sleep_time = datetime.combine(now.date(), sleep_time.time())

            if sleep_time < now:
                sleep_time += timedelta(days=1)

        except ValueError:
            return redirect("/")

        wake_times = calculate_wake_times(sleep_time)

        # 📜 Save history
        history.append({
            "input": sleep_input,
            "result": wake_times
        })

        if len(history) > MAX_HISTORY:
            history.pop(0)

    return render_template("index.html", wake_times=wake_times, history=history)


# 🧹 Clear History
@app.route("/clear")
def clear():
    history.clear()
    return redirect("/")





# 🚀 Run App
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)