"""CloudWatch Sentinel - a simple CloudWatch simulator built with Flask."""
import random
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from ml.anomaly_detector import AnomalyDetector

app = Flask(__name__)
detector = AnomalyDetector("data/metrics.csv")

# CloudWatch-style alarms: name -> (metric, threshold, message)
ALARMS = {
    "High CPU Usage": ("cpu", 80, "CPU utilization has exceeded 80%."),
    "High Memory Usage": ("memory", 85, "Memory utilization has exceeded 85%."),
    "High Response Time": ("response_time", 1000, "Response time has exceeded 1000 ms."),
}

# ---- in-memory state (no database needed) ----
history, logs, alerts = [], [], []
anomaly_count = 0
latest_anomaly = None
active_alarms = set()
mode = {"name": "normal", "ticks": 0}   # simulation mode, lasts a few ticks


def now():
    return datetime.now().strftime("%H:%M:%S")


def log(level, message):
    logs.append({"time": now(), "level": level, "message": message})
    del logs[:-50]  # keep only the last 50 lines


def generate_metrics():
    """Create one fake data point. The current mode decides how it looks."""
    cpu = random.gauss(45, 8)
    memory = random.gauss(55, 6)
    requests = random.gauss(150, 30)
    response = random.gauss(150, 30)

    if mode["ticks"] > 0:
        mode["ticks"] -= 1
        if mode["name"] == "cpu":
            cpu, response = random.uniform(88, 98), random.uniform(900, 1400)
        elif mode["name"] == "memory":
            memory, response = random.uniform(88, 97), random.uniform(500, 1100)
        elif mode["name"] == "traffic":
            requests, cpu = random.uniform(700, 950), random.uniform(70, 90)
            response = random.uniform(900, 1500)
    network = requests * 0.06 + random.uniform(0, 3)   # MB/s, roughly follows traffic

    return {
        "time": now(),
        "cpu": round(min(max(cpu, 1), 100), 1),
        "memory": round(min(max(memory, 1), 100), 1),
        "requests": int(max(requests, 0)),
        "response_time": int(max(response, 20)),
        "network": round(network, 1),
    }


def check_alarms(m):
    """Compare each metric with its threshold; log only when an alarm turns ON."""
    for name, (metric, limit, text) in ALARMS.items():
        if m[metric] > limit:
            if name not in active_alarms:
                active_alarms.add(name)
                alerts.append({"time": m["time"], "name": name, "message": text})
                log("WARNING" if metric != "response_time" else "ERROR", text)
        else:
            active_alarms.discard(name)


def new_tick():
    global anomaly_count, latest_anomaly
    m = generate_metrics()
    check_alarms(m)
    result = detector.predict(m["cpu"], m["memory"], m["requests"], m["response_time"])
    m["anomaly"] = result["is_anomaly"]
    m["score"] = result["score"]
    if m["anomaly"]:
        anomaly_count += 1
        latest_anomaly = m
        log("ERROR", f"Anomaly detected (CPU {m['cpu']}%, Memory {m['memory']}%)")
    elif random.random() < 0.3:
        log("INFO", random.choice(["Request received", "Health check passed",
                                   "Database connection established"]))
    history.append(m)
    del history[:-60]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/metrics")
def metrics():
    """Frontend calls this every 2 seconds: makes a new data point and returns data."""
    new_tick()
    return jsonify({"latest": history[-1], "history": history[-30:],
                    "active_alerts": len(active_alarms), "alerts": alerts[-6:][::-1]})


@app.route("/logs")
def get_logs():
    return jsonify(logs[-15:][::-1])


@app.route("/anomaly")
def anomaly():
    last = history[-1] if history else None
    return jsonify({"status": "Anomaly" if last and last["anomaly"] else "Normal",
                    "count": anomaly_count, "latest": latest_anomaly,
                    "points": [{"x": h["cpu"], "y": h["response_time"], "anomaly": h["anomaly"]}
                               for h in history[-40:]]})


@app.route("/simulate", methods=["POST"])
def simulate():
    global anomaly_count, latest_anomaly
    kind = (request.get_json() or {}).get("type")
    if kind == "reset":
        history.clear(); logs.clear(); alerts.clear(); active_alarms.clear()
        anomaly_count, latest_anomaly = 0, None
        mode.update(name="normal", ticks=0)
        log("INFO", "Data reset")
    elif kind in ("cpu", "memory", "traffic"):
        mode.update(name=kind, ticks=8)
        log("INFO", f"Simulation started: {kind}")
    return jsonify({"ok": True})


if __name__ == "__main__":
    log("INFO", "Server started successfully")
    app.run(debug=True)
