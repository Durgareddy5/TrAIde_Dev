import numpy as np

def build_features(predicted_price, last_price, volume):
    return np.array([
        predicted_price,
        last_price,
        volume
    ]).reshape(1, -1)