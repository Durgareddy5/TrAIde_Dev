from app.data.fetch import fetch_multi
from app.data.preprocess import fit_scaler
from app.core.config import SYMBOLS

data = fetch_multi(SYMBOLS)

all_close = []

for s in SYMBOLS:
    df = data[s].dropna()
    all_close.extend(df['Close'].values)

import numpy as np
all_close = np.array(all_close).reshape(-1,1)

fit_scaler(all_close)

print("Scaler saved ✅")