from tensorflow.keras.models import load_model
import xgboost as xgb
from app.core.config import MODEL_PATHS

lstm_model = None
xgb_model = None

def load_models():
    global lstm_model, xgb_model

    if lstm_model is None:
        lstm_model = load_model(MODEL_PATHS["lstm"], compile=False)

    if xgb_model is None:
        xgb_model = xgb.XGBClassifier()
        xgb_model.load_model(MODEL_PATHS["xgb"])

    return lstm_model, xgb_model