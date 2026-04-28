import numpy as np
import pandas as pd
import yfinance as yf
import joblib

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler

try:
    from app.core.config import SYMBOLS, SEQ_LENGTH
except Exception:
    SYMBOLS = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "ITC.NS",
        "BHARTIARTL.NS",
        "SBIN.NS",
        "WIPRO.NS",
        "SUNPHARMA.NS",
        "LT.NS",
        "^NSEI",
        "^NSEBANK",
        "^BSESN",
        "^INDIAVIX",
        "^CNX100",
        "^CRSLDX",
        "^CNXIT",
        "^CNXPHARMA",
        "^CNXAUTO",
        "^CNXFMCG",
        "^CNXMETAL",
        "^CNXREALTY",
        "^CNXENERGY",
        "^CNXINFRA",
        "^CNXPSUBANK",
        "^NSEMDCP50",
        "^NSMIDCP",
        "^CNXSC",
    ]
    SEQ_LENGTH = 60

all_data = []

# -------- FETCH + FEATURE ENGINEERING --------
for symbol in SYMBOLS:
    df = yf.download(symbol, period="20y", interval="1d")
    df.dropna(inplace=True)

    # Features
    df["returns"] = df["Close"].pct_change()
    df["ema_20"] = df["Close"].ewm(span=20).mean()
    df["ema_50"] = df["Close"].ewm(span=50).mean()
    df["vol_change"] = df["Volume"].pct_change()

    # pct_change can introduce inf/-inf (e.g. previous volume = 0)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    df.dropna(inplace=True)

    features = df[["returns", "ema_20", "ema_50", "vol_change"]]
    all_data.append(features)

# Combine all stocks
data = pd.concat(all_data)

# -------- SCALING --------
scaler = MinMaxScaler()
scaled = scaler.fit_transform(data)

joblib.dump(scaler, "saved_models/scaler.save")

# -------- CREATE SEQUENCES --------
X, y = [], []

for i in range(len(scaled) - SEQ_LENGTH):
    X.append(scaled[i:i+SEQ_LENGTH])
    y.append(scaled[i+SEQ_LENGTH][0])  # predict return

X, y = np.array(X), np.array(y)

# -------- MODEL --------
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(SEQ_LENGTH, X.shape[2])),
    Dropout(0.2),
    LSTM(64),
    Dropout(0.2),
    Dense(1)
])

model.compile(optimizer="adam", loss="mse")

model.fit(X, y, epochs=25, batch_size=32, validation_split=0.2)

model.save("saved_models/lstm.h5")

print("✅ LSTM trained and saved")