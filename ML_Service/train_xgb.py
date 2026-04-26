import xgboost as xgb
import numpy as np

# Dummy features (must match inference shape: 3 features)
X = np.random.rand(200, 3)

# Labels: 0=SELL, 1=HOLD, 2=BUY
y = np.random.randint(0, 3, 200)

model = xgb.XGBClassifier(n_estimators=10)
model.fit(X, y)

model.save_model("saved_models/xgb.json")

print("XGBoost model saved ✅")