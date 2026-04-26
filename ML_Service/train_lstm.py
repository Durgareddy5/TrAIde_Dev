import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler

# Dummy data (just to create valid model)
data = np.random.rand(500, 1)

scaler = MinMaxScaler()
data = scaler.fit_transform(data)

SEQ_LENGTH = 60

X, y = [], []
for i in range(len(data) - SEQ_LENGTH):
    X.append(data[i:i+SEQ_LENGTH])
    y.append(data[i+SEQ_LENGTH])

X, y = np.array(X), np.array(y)

model = Sequential()
model.add(LSTM(50, input_shape=(SEQ_LENGTH, 1)))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')

model.fit(X, y, epochs=1)

model.save("saved_models/lstm.h5")

print("Valid LSTM saved ✅")