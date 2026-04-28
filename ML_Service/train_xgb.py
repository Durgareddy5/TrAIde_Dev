import numpy as np
import pandas as pd
import yfinance as yf
import xgboost as xgb

from sklearn.utils.class_weight import compute_class_weight
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from collections import Counter

# -------- CONFIG --------
SYMBOLS = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "ITC.NS","BHARTIARTL.NS","SBIN.NS","WIPRO.NS","SUNPHARMA.NS",
    "LT.NS","^NSEI","^NSEBANK","^BSESN"
]

all_features = []
all_labels = []

# -------- DATA PREP --------
for symbol in SYMBOLS:
    print(f"Processing {symbol}...")

    df = yf.download(symbol, period="5y", interval="1d")

    if df.empty:
        print(f"⚠️ Skipping {symbol}")
        continue

    # Flatten columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if "Volume" not in df.columns:
        df["Volume"] = 0

    df = df[["Close", "Volume"]].copy()
    df.dropna(inplace=True)

    # -------- FEATURES --------
    df["returns"] = df["Close"].pct_change()
    df["ema_20"] = df["Close"].ewm(span=20).mean()
    df["ema_50"] = df["Close"].ewm(span=50).mean()
    df["vol_change"] = df["Volume"].pct_change()

    df["trend"] = df["ema_20"] - df["ema_50"]
    df["momentum"] = df["Close"] - df["Close"].shift(5)
    df["volatility"] = df["returns"].rolling(10).std()

    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    df["returns"] = df["returns"].clip(-0.2, 0.2)
    df["vol_change"] = df["vol_change"].clip(-1, 1)

    # -------- LABELS --------
    df["future_return"] = df["returns"].shift(-1)
    vol = df["returns"].rolling(20).std()

    df["label"] = np.where(df["future_return"] > vol, 2,
                   np.where(df["future_return"] < -vol, 0, 1))

    df.dropna(inplace=True)

    # -------- COLLECT --------
    features = df[[
        "returns","ema_20","ema_50","vol_change",
        "trend","momentum","volatility"
    ]].values

    labels = df["label"].values

    all_features.extend(features)
    all_labels.extend(labels)

# -------- FINAL DATA --------
X = np.array(all_features)
y = np.array(all_labels)

print("\n📊 Data Shape:", X.shape)
print("📊 Label Distribution:", Counter(y))

# -------- TRAIN / TEST SPLIT --------
# IMPORTANT: shuffle=False (time series data)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False
)

# -------- CLASS BALANCING --------
classes = np.unique(y_train)
weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_train)
class_weights = dict(zip(classes, weights))

sample_weights = np.array([class_weights[label] for label in y_train])

# -------- MODEL --------
model = xgb.XGBClassifier(
    tree_method="hist",
    n_estimators=400,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    num_class=3,
    eval_metric="mlogloss"
)

# -------- TRAIN --------
model.fit(X_train, y_train, sample_weight=sample_weights)

# -------- PREDICT --------
y_pred = model.predict(X_test)

# -------- EVALUATION --------
accuracy = accuracy_score(y_test, y_pred)

print("\n✅ Accuracy:", round(accuracy * 100, 2), "%")

print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred, target_names=["SELL","HOLD","BUY"]))

print("\n📊 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# -------- SAVE MODEL --------
model.save_model("saved_models/xgb.json")

print("\n✅ Model trained, evaluated, and saved successfully!")