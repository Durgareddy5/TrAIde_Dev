import numpy as np
import pandas as pd
import yfinance as yf
import joblib

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler

# -------- CONFIG --------
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

all_features = []
all_targets = []

# -------- FETCH + FEATURE ENGINEERING --------
for symbol in SYMBOLS:
    print(f"Processing {symbol}...")

    df = yf.download(symbol, period="20y", interval="1d")

    if df.empty:
        print(f"⚠️ Skipping {symbol}")
        continue

    # ✅ Flatten columns (VERY IMPORTANT)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Ensure required columns
    if "Volume" not in df.columns:
        df["Volume"] = 0

    df = df[["Close", "Volume"]].copy()
    df.dropna(inplace=True)

    # -------- FEATURES --------
    df["returns"] = df["Close"].pct_change()

    # ✅ Smooth returns (reduce noise)
    df["returns"] = df["returns"].rolling(3).mean()

    df["ema_20"] = df["Close"].ewm(span=20).mean()
    df["ema_50"] = df["Close"].ewm(span=50).mean()
    df["vol_change"] = df["Volume"].pct_change()

    # -------- CLEAN --------
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    # Clip extreme values
    df["returns"] = df["returns"].clip(-0.2, 0.2)
    df["vol_change"] = df["vol_change"].clip(-1, 1)

    # -------- PREPARE DATA --------
    features = df[["returns", "ema_20", "ema_50", "vol_change"]]

    # ✅ FIX: skip empty / insufficient data
    if features.shape[0] < SEQ_LENGTH:
        print(f"⚠️ Skipping {symbol} (not enough data after cleaning)")
        continue

    # ✅ SCALE ONLY INPUT FEATURES
    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(features)

    # Clip scaled values for safety
    scaled_features = np.clip(scaled_features, 0, 1)

    # -------- SEQUENCE CREATION --------
    for i in range(len(scaled_features) - SEQ_LENGTH):
        X_seq = scaled_features[i:i+SEQ_LENGTH]

        # ✅ TARGET = REAL RETURN (NOT SCALED)
        y_target = df["returns"].values[i + SEQ_LENGTH]

        all_features.append(X_seq)
        all_targets.append(y_target)

# -------- FINAL DATA --------
X = np.array(all_features)
y = np.array(all_targets)

print(f"Training shape: {X.shape}, {y.shape}")

# -------- MODEL --------
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(SEQ_LENGTH, X.shape[2])),
    Dropout(0.2),
    LSTM(64),
    Dropout(0.2),
    Dense(1)
])

model.compile(optimizer="adam", loss="mse")

# ✅ TRAIN LONGER FOR STABILITY
model.fit(
    X, y,
    epochs=40,
    batch_size=32,
    validation_split=0.2
)

# -------- SAVE --------
model.save("saved_models/lstm.h5")
joblib.dump(scaler, "saved_models/scaler.save")

print("✅ LSTM trained and saved successfully")