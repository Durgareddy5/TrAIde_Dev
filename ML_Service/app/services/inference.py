from app.core.loader import load_models
from app.data.fetch import fetch_multi, fetch_recent
from app.data.preprocess import load_scaler, transform, reshape_lstm
from app.services.feature_engineering import build_features
from app.core.config import SYMBOLS, SEQ_LENGTH

def run_prediction():
    lstm, xgb = load_models()
    scaler = load_scaler()

    hist = fetch_multi(SYMBOLS)
    recent = fetch_recent(SYMBOLS)

    results = []

    for symbol in SYMBOLS:
        try:
            df_hist = hist[symbol].dropna()
            close = df_hist['Close'].values.reshape(-1,1)

            scaled = transform(close, scaler)

            if len(scaled) < SEQ_LENGTH:
                continue

            last_seq = reshape_lstm(scaled[-SEQ_LENGTH:])
            pred_scaled = lstm.predict(last_seq, verbose=0)

            pred_price = scaler.inverse_transform(pred_scaled)[0][0]

            df_recent = recent[symbol].dropna()
            last_price = df_recent['Close'].iloc[-1]
            volume = df_recent['Volume'].mean()

            features = build_features(pred_price, last_price, volume)

            decision = xgb.predict(features)[0]
            action = ["SELL", "HOLD", "BUY"][decision]

            results.append({
                "symbol": symbol,
                "predicted_price": float(pred_price),
                "last_price": float(last_price),
                "action": action
            })

        except Exception as e:
            results.append({
                "symbol": symbol,
                "error": str(e)
            })

    return results