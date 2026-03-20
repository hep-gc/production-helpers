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

#print(df.shape)
#print(df.head(50))

#----PREPARE DATA------
train_frac = 0.8
n_rows = len(df)
n_train = int(n_rows * train_frac)

# Split
df_test = df['2025-11-01':'2026-01-01']
df_train  = df[:'2025-11-01']
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
x_train, _ = create_window(df_train_scaled, lookback)
x_test, _  = create_window(df_test_scaled, lookback)

# target = input
train_dataset = data.TensorDataset(x_train, x_train)
test_dataset  = data.TensorDataset(x_test, x_test)
#print(x_train[0])
#print(y_train[0])

print(x_train.shape)
print(x_test.shape)


#-------CREATE MODEL------------

class Autoencoder(nn.Module):
    def __init__(self, features, hidden_size=128, num_layers=2):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # Encoder
        self.encoder = nn.LSTM(input_size=features,
                               hidden_size=hidden_size,
                               num_layers=num_layers,
                               batch_first=True)

        # Decoder
        self.decoder = nn.LSTM(input_size=hidden_size,
                               hidden_size=hidden_size,
                               num_layers=num_layers,
                               batch_first=True)

        # Final output
        self.output_layer = nn.Linear(hidden_size, features)

    def forward(self, x):
        # Encoder
        _, (h_n, c_n) = self.encoder(x)  # take only last hidden/cell state

        # Repeat last hidden state across sequence length
        seq_len = x.size(1)
        decoder_input = h_n[-1].unsqueeze(1).repeat(1, seq_len, 1)  # [batch, seq_len, hidden]

        # Decoder
        decoded, _ = self.decoder(decoder_input)
        out = self.output_layer(decoded)
        return out

#----------TRAINING-------------

model=Autoencoder(features=200)
optimizer = optim.Adam(model.parameters())
loss_fn = nn.MSELoss()
loader = data.DataLoader(train_dataset, batch_size=60, shuffle=True)

n_epochs = 50

for epoch in range(n_epochs):
    model.train()
    for x_batch, _ in loader:
        y_pred = model(x_batch)
        loss = loss_fn(y_pred, x_batch)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        recon_train = model(x_train)
        recon_test = model(x_test)
        train_rmse = torch.sqrt(loss_fn(recon_train, x_train)).item()
        test_rmse = torch.sqrt(loss_fn(recon_test, x_test)).item()
        test_error = torch.mean((recon_test - x_test)**2, dim=(1,2))
    print(f"Epoch {epoch}: train RMSE {train_rmse:.4f} | test RMSE {test_rmse:.4f}")

exit()
