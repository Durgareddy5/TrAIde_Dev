import numpy as np
import pandas as pd
import yfinance as yf
import xgboost as xgb

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

for symbol in SYMBOLS:
    print(f"Processing {symbol}...")

    df = yf.download(symbol, period="20y", interval="1d")


    if df.empty:
        print(f"⚠️ Skipping {symbol} (no data)")
        continue

    # ✅ FIX 1: Flatten columns (important)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Close", "Volume"]].copy()
    df.dropna(inplace=True)

    # -------- FEATURES --------
    df["returns"] = df["Close"].pct_change()
    df["ema_20"] = df["Close"].ewm(span=20).mean()
    df["ema_50"] = df["Close"].ewm(span=50).mean()
    df["vol_change"] = df["Volume"].pct_change()

    df.dropna(inplace=True)

    # -------- LABELS (VECTOR FIX) --------
    df["future_return"] = df["Close"].pct_change().shift(-1)

    def label_fn(x):
        if x > 0.01:
            return 2  # BUY
        elif x < -0.01:
            return 0  # SELL
        else:
            return 1  # HOLD

    df["label"] = df["future_return"].apply(label_fn)

    # Remove NaN
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    
    # Clip extreme values (VERY IMPORTANT)
    df["returns"] = df["returns"].clip(-0.2, 0.2)
    df["vol_change"] = df["vol_change"].clip(-1, 1)

    # -------- COLLECT --------
    features = df[["returns", "ema_20", "ema_50", "vol_change"]].values
    labels = df["label"].values

    all_features.extend(features)
    all_labels.extend(labels)

# -------- FINAL DATA --------
X = np.array(all_features)
y = np.array(all_labels)

print(f"Training data shape: {X.shape}")

# -------- MODEL --------
model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softmax",
    num_class=3,
    eval_metric="mlogloss"
)

model.fit(X, y)

# -------- SAVE --------
model.save_model("saved_models/xgb.json")

print("✅ XGBoost retrained successfully")