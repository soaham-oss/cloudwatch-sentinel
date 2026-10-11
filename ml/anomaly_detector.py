"""Anomaly detection with Isolation Forest (scikit-learn)."""
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURES = ["cpu", "memory", "requests", "response_time"]


def make_training_data(path, rows=500):
    """Create a CSV of NORMAL server behaviour the model learns from."""
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "cpu": rng.normal(45, 10, rows).clip(5, 75),
        "memory": rng.normal(55, 8, rows).clip(20, 78),
        "requests": rng.normal(150, 40, rows).clip(20, 300),
        "response_time": rng.normal(150, 40, rows).clip(40, 350),
    }).round(1)
    df.to_csv(path, index=False)


class AnomalyDetector:
    def __init__(self, csv_path="data/metrics.csv"):
        if not os.path.exists(csv_path):
            make_training_data(csv_path)
        data = pd.read_csv(csv_path)[FEATURES]
        # contamination = share of training points we expect to be unusual
        self.model = IsolationForest(n_estimators=100, contamination=0.02, random_state=42)
        self.model.fit(data)

    def predict(self, cpu, memory, requests, response_time):
        point = pd.DataFrame([[cpu, memory, requests, response_time]], columns=FEATURES)
        label = self.model.predict(point)[0]            # 1 = normal, -1 = anomaly
        score = self.model.decision_function(point)[0]  # lower = more unusual
        return {"is_anomaly": bool(label == -1), "score": round(float(score), 3)}
