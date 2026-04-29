import numpy as np
import pandas as pd
import yfinance as yf

from app.core.loader import load_models
from app.core.config import SYMBOLS, SEQ_LENGTH
from app.services.feature_engineering import add_features

def run_prediction():
    lstm, xgb, scaler = load_models()
    results = []

    for symbol in SYMBOLS:
        try:
            print(f"Processing {symbol}")

            df = yf.download(symbol, period="20y", interval="1d")

            # flatten columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # ensure Volume exists
            if "Volume" not in df.columns:
                df["Volume"] = 0

            df = df[["Close", "Volume"]].copy()
            df.dropna(inplace=True)
            

            df = add_features(df)

            if len(df) < SEQ_LENGTH:
                continue

            features = df[["returns", "ema_20", "ema_50", "vol_change"]]
            features = features.fillna(0)

            scaled = scaler.transform(features)

            last_seq = scaled[-SEQ_LENGTH:]
            last_seq = np.reshape(last_seq, (1, SEQ_LENGTH, scaled.shape[1]))

            pred_return = float(lstm.predict(last_seq, verbose=0)[0][0])

            # safety clamp
            if abs(pred_return) > 0.05:
                pred_return = 0

            last_price = float(df["Close"].iloc[-1].item())
            predicted_price = last_price * (1 + pred_return)

            # XGBoost decision
            xgb_input = scaled[-1].reshape(1, -1)
            action = int(xgb.predict(xgb_input)[0])

            action_map = {0: "SELL", 1: "HOLD", 2: "BUY"}

            results.append({
                "symbol": symbol,
                "predicted_price": round(predicted_price, 2),
                "last_price": round(last_price, 2),
                "action": action_map[action]
            })

        except Exception as e:
            results.append({
                "symbol": symbol,
                "error": str(e)
            })

    return results