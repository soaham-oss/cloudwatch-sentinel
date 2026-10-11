# CloudWatch Sentinel – AWS Cloud Monitoring and Anomaly Detection Simulator

A small Flask web app that **simulates Amazon CloudWatch**: live metrics, logs, threshold alarms and a dashboard, plus one ML enhancement – **anomaly detection with Isolation Forest**. No real AWS account is needed; all data is simulated.

## What is Amazon CloudWatch?
CloudWatch is AWS's monitoring service. It collects and shows data about your cloud resources and applications.
- **Metrics** – numbers over time (CPU, memory, network, requests).
- **Logs** – text records of what happened (INFO / WARNING / ERROR).
- **Alarms** – rules like "CPU > 80%" that raise an alert.
- **Dashboards** – one screen showing all of the above.
- **Monitoring** – watching these continuously so problems are found early.

## Features
- Dashboard cards: CPU, memory, network, requests, response time, active alerts
- Live Chart.js graphs (update every 2 seconds, no page refresh)
- Alarms: CPU > 80%, Memory > 85%, Response time > 1000 ms
- Live log panel
- AI Anomaly Detection panel (status, count, latest anomaly, normal-vs-anomaly graph)
- Controls: Start/Stop Monitoring, Simulate High CPU / High Memory / Traffic Spike, Reset Data

## ML explanation
**Anomaly detection** finds data points that look unusual compared with normal behaviour. In cloud monitoring it catches problems that a single fixed threshold can miss (e.g. a strange *combination* of values).

**Isolation Forest** builds many random decision trees. Each tree splits the data at random values. Unusual points are different from the rest, so they get separated (isolated) in very few splits; normal points need many splits. Short path = anomaly.

**Features:** CPU, memory, request count, response time.
**Training data:** `data/metrics.csv` (normal behaviour, auto-created on first run).
**Output:** `Normal` or `Anomaly` for every new data point.

## Technology stack
HTML, CSS, JavaScript, Chart.js · Python, Flask · scikit-learn (IsolationForest), pandas

## Architecture
Browser (HTML/CSS/JS) → Flask API → metric simulation → alarm checks → Isolation Forest → dashboard alerts

API: `GET /metrics`, `GET /logs`, `GET /anomaly`, `POST /simulate`

## Run locally
```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Using the dashboard
Monitoring starts automatically. Click **Simulate High CPU** to see the alarm fire, the log fill with warnings, and the AI panel turn red. **Reset Data** clears everything.

## Future improvements
Email/SNS-style notifications, saving history to a database, more metrics, adjustable thresholds, deployment to AWS EC2/Elastic Beanstalk.
