import pandas as pd

def prepare_features(df: pd.DataFrame):
    # expects columns: file_size_mb, transfer_time_sec
    X = df[["file_size_mb"]]
    y = df["transfer_time_sec"]
    return X, y
