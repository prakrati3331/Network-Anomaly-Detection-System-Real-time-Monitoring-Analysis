import joblib
import numpy as np
import pandas as pd
import os

_model = None
_scaler = None

def load_models(model_path=None, scaler_path=None):
    global _model, _scaler
    
    # If no paths are provided, use default paths relative to the project root
    if model_path is None or scaler_path is None:
        # Get the absolute path to the models directory
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        MODEL_DIR = os.path.join(BASE_DIR, 'models')
        model_path = os.path.join(MODEL_DIR, 'latest_model.joblib')
        scaler_path = os.path.join(MODEL_DIR, 'latest_scaler.joblib')
    
    print(f"🔍 Loading model from: {model_path}")
    print(f"🔍 Loading scaler from: {scaler_path}")
    
    _model = joblib.load(model_path)
    _scaler = joblib.load(scaler_path)

def preprocess_input(df):
    """df: DataFrame of numeric features"""
    df = df.select_dtypes(include=[np.number]).fillna(method='ffill').fillna(0)
    return df

def score_batch(df):
    if _model is None or _scaler is None:
        raise RuntimeError("Model/scaler not loaded. Call load_models() first.")
    X = preprocess_input(df)
    Xs = _scaler.transform(X)
    # anomaly score: lower -> more abnormal according to sklearn (but sklearn's score_samples: higher = less abnormal)
    # IsolationForest: predict -> -1 anomaly, 1 normal
    preds = _model.predict(Xs)  # -1 anomaly, 1 normal
    scores = _model.score_samples(Xs)  # higher == less abnormal
    # convert to intuitive anomaly score: 1 = anomalous, 0 = normal
    is_anomaly = (preds == -1).astype(int)
    return pd.DataFrame({
        "anomaly": is_anomaly,
        "score": scores
    }, index=df.index)
