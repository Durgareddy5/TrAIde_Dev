import numpy as np
import pandas as pd
import yfinance as yf
import xgboost as xgb

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

all_features = []
all_labels = []

# -------- DATA PREP --------
for symbol in SYMBOLS:
    print(f"Processing {symbol}...")

    df = yf.download(symbol, period="20y", interval="1d")

    if df.empty:
        print(f"⚠️ Skipping {symbol}")
        continue

    # ✅ Flatten columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Ensure required columns
    if "Volume" not in df.columns:
        df["Volume"] = 0

    df = df[["Close", "Volume"]].copy()
    df.dropna(inplace=True)

    # -------- FEATURES (MATCH LSTM) --------
    df["returns"] = df["Close"].pct_change()

    # ✅ smoothing (same as LSTM)
    df["returns"] = df["returns"].rolling(3).mean()

    df["ema_20"] = df["Close"].ewm(span=20).mean()
    df["ema_50"] = df["Close"].ewm(span=50).mean()
    df["vol_change"] = df["Volume"].pct_change()

    # -------- CLEAN --------
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    df["returns"] = df["returns"].clip(-0.2, 0.2)
    df["vol_change"] = df["vol_change"].clip(-1, 1)

    # -------- LABELS --------
    df["future_return"] = df["returns"].shift(-1)

    def label_fn(x):
        if x > 0.005:
            return 2   # BUY
        elif x < -0.005:
            return 0   # SELL
        else:
            return 1   # HOLD

    df["label"] = df["future_return"].apply(label_fn)

    df.dropna(inplace=True)

    # -------- COLLECT --------
    features = df[["returns", "ema_20", "ema_50", "vol_change"]].values
    labels = df["label"].values

    all_features.extend(features)
    all_labels.extend(labels)

# -------- FINAL DATA --------
X = np.array(all_features)
y = np.array(all_labels)

print(f"Training data shape: {X.shape}")

# -------- CHECK DISTRIBUTION --------
from collections import Counter
print("Label distribution:", Counter(y))

# -------- MODEL --------
model = xgb.XGBClassifier(
    tree_method="hist",
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",   # probabilities for better decisions
    num_class=3,
    eval_metric="mlogloss"
)

# -------- TRAIN --------
model.fit(X, y)

# -------- SAVE --------
model.save_model("saved_models/xgb.json")

print("✅ XGBoost trained and saved successfully")