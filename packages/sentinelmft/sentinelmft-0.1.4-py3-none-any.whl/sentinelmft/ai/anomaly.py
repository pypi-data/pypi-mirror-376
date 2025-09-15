import pandas as pd
from sklearn.ensemble import IsolationForest
from joblib import dump, load

MODEL_DEF = {"n_estimators": 100, "contamination": "auto", "random_state": 42}

def train_anomaly(csv_path: str, model_out: str):
    df = pd.read_csv(csv_path)
    feats = df[["file_size_mb", "transfer_time_sec"]]
    model = IsolationForest(**MODEL_DEF).fit(feats)
    dump(model, model_out)
    return model_out

def score_anomaly(csv_path: str, model_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path).copy()
    model = load(model_path)
    feats = df[["file_size_mb", "transfer_time_sec"]]
    df["anomaly_score"] = model.decision_function(feats)
    df["is_anomaly"] = model.predict(feats) == -1
    return df

