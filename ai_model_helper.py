import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import requests

MODEL_PATH = "ai_model.pkl"

def train_from_twelvedata(api_key):
    try:
        symbol = "EURUSD"
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=800&apikey={api_key}"
        r = requests.get(url, timeout=15).json()
        if "values" not in r:
            return None
        df = pd.DataFrame(r["values"]).iloc[::-1]
        df = df.astype({"open":"float","high":"float","low":"float","close":"float"})
        df["ema5"] = df["close"].ewm(span=5).mean()
        df["ema10"] = df["close"].ewm(span=10).mean()
        delta = df["close"].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100/(1+rs))
        df["atr"] = (df["high"] - df["low"]).rolling(14).mean()
        df.dropna(inplace=True)
        X = df[["ema5","ema10","rsi","atr"]].values[:-1]
        y = (df["close"].shift(-1) > df["close"]).astype(int).values[:-1]
        if len(X) < 200:
            return None
        model = RandomForestClassifier(n_estimators=150, random_state=42)
        model.fit(X, y)
        joblib.dump(model, MODEL_PATH)
        return model
    except Exception as e:
        print("train_from_twelvedata failed:", e)
        return None

def train_synthetic():
    rng = np.random.RandomState(42)
    n = 2000
    X = rng.normal(size=(n,4))
    y = (X[:,0] + 0.1*X[:,1] + 0.2*X[:,2] + rng.normal(scale=0.2,size=n) > 0).astype(int)
    model = RandomForestClassifier(n_estimators=80, random_state=42)
    model.fit(X,y)
    joblib.dump(model, MODEL_PATH)
    return model

def load_or_create_model(api_key):
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            pass
    m = train_from_twelvedata(api_key)
    if m is not None:
        return m
    return train_synthetic()