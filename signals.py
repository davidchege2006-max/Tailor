import os
import pandas as pd
import requests
import numpy as np
from ai_model_helper import load_or_create_model

class SignalEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = load_or_create_model(api_key)

    def fetch_ohlc(self, pair, interval='1min', outputsize=200):
        symbol = pair.replace('/','')
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={self.api_key}"
        r = requests.get(url, timeout=10).json()
        if "values" not in r:
            return None
        df = pd.DataFrame(r["values"]).iloc[::-1]
        for c in ['open','high','low','close']:
            df[c] = df[c].astype(float)
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df

    def compute_features(self, df):
        df = df.copy()
        df['ema5'] = df['close'].ewm(span=5).mean()
        df['ema10'] = df['close'].ewm(span=10).mean()
        delta = df['close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi'] = 100 - (100/(1+rs))
        df['atr'] = (df['high'] - df['low']).rolling(14).mean()
        return df.dropna()

    def predict_next(self, pair, interval='1min'):
        df = self.fetch_ohlc(pair, interval=interval, outputsize=300)
        if df is None or df.empty:
            return None
        feats = self.compute_features(df)
        if len(feats) < 20:
            return None
        X = feats[['ema5','ema10','rsi','atr']].values
        last = X[-1].reshape(1,-1)
        pred = int(self.model.predict(last)[0])
        proba = float(self.model.predict_proba(last)[0][pred]) * 100 if hasattr(self.model,'predict_proba') else 0.0
        entry = float(feats['close'].iloc[-1])
        atr = float(feats['atr'].iloc[-1])
        if pred == 1:
            signal = "BUY"
            stop = entry - atr
            tp = entry + atr
        else:
            signal = "SELL"
            stop = entry + atr
            tp = entry - atr
        return {"pair": pair, "interval": interval, "signal": signal, "entry": entry, "stop": stop, "tp": tp, "confidence": proba}