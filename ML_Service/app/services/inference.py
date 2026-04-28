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

            # -------- FETCH DATA --------
            df = yf.download(symbol, period="20y", interval="1d")

            if df.empty:
                results.append({"symbol": symbol, "error": "No data"})
                continue

            # Flatten columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Ensure Volume exists
            if "Volume" not in df.columns:
                df["Volume"] = 0

            df = df[["Close", "Volume"]].copy()
            df.dropna(inplace=True)

            # -------- BASE FEATURES --------
            df = add_features(df)

            # Ensure enough data
            if len(df) < SEQ_LENGTH:
                results.append({"symbol": symbol, "error": "Not enough data"})
                continue

            # =========================================================
            # 🔵 LSTM PIPELINE (4 FEATURES + SCALER)
            # =========================================================
            features_lstm = df[[
                "returns",
                "ema_20",
                "ema_50",
                "vol_change"
            ]].fillna(0)

            scaled = scaler.transform(features_lstm)

            last_seq = scaled[-SEQ_LENGTH:]
            last_seq = np.reshape(last_seq, (1, SEQ_LENGTH, scaled.shape[1]))

            pred_return = float(lstm.predict(last_seq, verbose=0)[0][0])

            # Safety clamp
            if abs(pred_return) > 0.05:
                pred_return = 0

            last_price = float(df["Close"].iloc[-1])
            predicted_price = last_price * (1 + pred_return)

            # =========================================================
            # 🔴 XGBOOST PIPELINE (7 FEATURES — NO SCALER)
            # =========================================================

            # Add missing features (must match training)
            df["trend"] = df["ema_20"] - df["ema_50"]
            df["momentum"] = df["Close"] - df["Close"].shift(5)
            df["volatility"] = df["returns"].rolling(10).std()

            df.dropna(inplace=True)

            xgb_features = df[[
                "returns",
                "ema_20",
                "ema_50",
                "vol_change",
                "trend",
                "momentum",
                "volatility"
            ]].fillna(0)

            xgb_input = xgb_features.iloc[-1].values.reshape(1, -1)

            # Debug (optional)
            # print("XGB feature length:", len(xgb_input[0]))

            action = int(xgb.predict(xgb_input)[0])

            action_map = {
                0: "SELL",
                1: "HOLD",
                2: "BUY"
            }

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