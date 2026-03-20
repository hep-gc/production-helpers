
import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.utils.data as data
import torch.optim as optim

df = pd.read_csv('raw_yearly_metrics.csv', index_col="Datetime", parse_dates=True)

# Drop features with zero variance
df = df.loc[:, df.std() > 0]

#df = df['2026-02-08':'2026-02-08']
#print(df.head(50))

#print(df.shape)
#print(df.head(50))

#----PREPARE DATA------
train_frac = 0.8
n_rows = len(df)
n_train = int(n_rows * train_frac)

# Split
df_test = df['2026-01-08':'2026-01-08'] #from 19th fails no data from 18th
df_train  = df[:'2025-06-01']
#df_train = df.iloc[:n_train]   # first 80% of rows
#df_test  = df.iloc[n_train:]   # last 20% of rows

#scale values
scaler = StandardScaler()

df_train_scaled = scaler.fit_transform(df_train.values)
df_test_scaled = scaler.transform(df_test.values)

print("Train stats:", df_train_scaled.min(), df_train_scaled.max())
print("Test stats:", df_test_scaled.min(), df_test_scaled.max())
#print(np.max(df_test.values, axis=0))


#----WINDONW SIZE -----------

#convert dataframe into list of sequences
lookback = 5
features = 200
def create_window(dataset, lookback):
    x, y = [], []
    for i in range(len(dataset)-lookback):
        x.append(dataset[i:i+lookback])
        y.append(dataset[i+lookback])
    return torch.tensor(np.array(x), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

#create dataset

x_train, y_train= create_window(df_train_scaled, lookback=lookback)
x_test, y_test = create_window(df_test_scaled, lookback=lookback)

#print(x_train[0])
#print(y_train[0])

print(x_train.shape, y_train.shape)
print(x_test.shape, y_test.shape)


#-------CREATE MODEL------------
class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=features, hidden_size=128, num_layers=2, batch_first=True)
        self.linear = nn.Linear(128, 200)

    def forward(self, x):
        x, _ = self.lstm(x)
        x = x[:, -1, :]
        x = self.linear(x)
        return x

#----------TRAINING-------------

model=Model()
optimizer = optim.Adam(model.parameters())
loss_fn = nn.MSELoss()
loader = data.DataLoader(data.TensorDataset(x_train, y_train), shuffle=True, batch_size=60)

n_epochs = 50

for epoch in range(n_epochs):
    model.train()
    for x_batch, y_batch in loader:
        y_pred = model(x_batch)
        loss = loss_fn(y_pred, y_batch)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    if epoch % 1 != 0:
        continue
    model.eval()
    with torch.no_grad():
        y_pred = model(x_train)
        train_rmse = torch.sqrt(loss_fn(y_pred, y_train)).item()
        y_pred = model(x_test)
        test_rmse = torch.sqrt(loss_fn(y_pred, y_test)).item()
    print("Epoch %d: train RMSE %.4f | test RMSE %.4f" % (epoch, train_rmse, test_rmse))

exit()
with torch.no_grad():
    pred_series = np.full_like(df_train_scaled, np.nan)
    pred_series[lookback:]= model(x_train).numpy()

plt.plot(df_train_scaled[:, 2], c="b")
plt.plot(pred_series[:,2], c="r")
plt.savefig("ml/lstm_train_feature0.png")
plt.close()
