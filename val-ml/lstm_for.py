import math
import re
import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.utils.data as data
import torch.optim as optim
import torch.nn.functional as F
import seaborn as sns

#to display all columns or rows

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.float_format', '{:.3f}'.format)

#-------variables------------------
#----------------------------------
csv = 'raw_year_features_belle.csv'
lookback = 144
layers = 2
hidden_l = 12
n_epochs = 55

match = re.search(r"raw_year_features_(.+)\.csv", csv)
if match:
    vm = match.group(1)
#----------------------------------
#----------------------------------
#load data
def load_data(csv):
    return pd.read_csv(csv, index_col="Datetime", parse_dates=True)

df = load_data(csv)

#clean data
def clean_data(df):
    df = np.log1p(df)
    low_var_cols = df.columns[df.std() < 0.01]
    print(low_var_cols)
    df = df.drop(columns=low_var_cols)
    return df

#-----------PREPARE DATA----------------------
#--------------------------------------------

df = clean_data(df)
df = df.drop(columns=['load_fifteen', 'load_five', 'storage-RDC refer size'])

print("OVERVIEW DATAFRAME:\n")
print(df.describe().transpose())
print("\n")

#split data
df_test = df['2025-11-02':]
df_train  = df[:'2025-11-01']

#scale values
train_mean = df_train.mean()
train_std = df_train.std()

#df_train_vls = (df_train - train_mean) / train_std
#df_test_vls = (df_test - train_mean) / train_std

#print(f"TEST DATAFRAME AFTER SCALING\n")
#print(df_test_vls.describe().transpose())
#print(f"\n")
#print(f"TRAIN DATAFRAME AFTER SCALIN\n")
#print(df_train_vls.describe().transpose())

print("Train stats:", df_train.values.min(), df_train.values.max())
print("Test stats:", df_test.values.min(), df_test.values.max())
print("\n")

#----WINDONW SIZE -----------

#convert dataframe into list of sequences
features = df.shape[1]

def create_window(dataset, lookback):
    x, y = [], []
    for i in range(len(dataset)-lookback):
        x.append(dataset[i:i+lookback])
        y.append(dataset[i+lookback])
    return torch.tensor(np.array(x), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

#create dataset
x_train, y_train= create_window(df_train.values, lookback=lookback)
x_test, y_test = create_window(df_test.values, lookback=lookback)

print(x_train.shape, y_train.shape)
print(x_test.shape, y_test.shape)


#-------CREATE MODEL------------

class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=features, hidden_size=hidden_l, num_layers=layers, batch_first=True, dropout=0.3)
        self.linear = nn.Linear(hidden_l, features)

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

#----------eval results fucntions-----------------

#Get predictions
def get_prediction(df):
    """
    given a dataframe, converts to windows and returns prediction results
    """
    x_vals, y_vals= create_window(df.values, lookback=lookback)
    
    model.eval()
    with torch.no_grad():
        y_pred = model(x_vals)
    
    #df_temp = df[lookback:]
    df_temp = df.iloc[lookback:]
    #dataframe for predicted vals
    y_pred_np = y_pred.numpy()
    df_pred = pd.DataFrame(y_pred_np, index=df_temp.index)
    df_pred.columns = df.columns
    #print(df_pred.head(1))

    #dataframe for actual vals
    y_actual_np = y_vals.numpy()
    df_actual = pd.DataFrame(y_actual_np, index=df_temp.index)
    df_actual.columns = df.columns
    #print(df_actual.head(1))
    
    return df_pred, df_actual

def calculate_error(df_actual, df_pred):
    df_error = (df_actual - df_pred).abs()
    df_error['error_total'] = df_error.mean(axis=1)

    return df_error

def get_high_error_timestamps(df_error, top_n=50):
    # Separate feature errors from total error
    df_features = df_error.drop(columns=['error_total'])

    # Feature with highest error per row
    max_feature = df_features.idxmax(axis=1)

    # Value of that max error
    max_value = df_features.max(axis=1)

    # Total error
    total_error = df_error['error_total']

    # Combine everything
    summary = pd.DataFrame({
        'max_feature': max_feature,
        'max_feature_error': max_value,
        'error_total': total_error
    })

    # Sort by total error
    summary = summary.sort_values(by='error_total', ascending=False)

    # Top N
    print(summary.head(top_n))
    return summary.head(top_n)

def inspect_sequences(df_actual, df_recon, index_list):
    #df_recon = np.expm1(df_recon)
    #df_actual = np.expm1(df_actual)
    #df_recon = df_recon*train_max
    #df_actual = df_actual*train_max
    count = 0
    for index in index_list:
        data = {'actual': df_actual.loc[index], 'pred': df_recon.loc[index]}
        df = pd.DataFrame(data, index=df_actual.columns)
        if count <10:
            print(f"\n{index}\n")
            print(df.head(40))
        count = count+1

#-----------REVIEW RESULTS--------------------------
#--------------------------------------------------
df_pred, df_actual = get_prediction(df_test)

#new_index = "2026-02-08 11:20:00"
#print(f"pred vals: {df_pred.loc[new_index]}\n")
#print(f"actual vals: {df_actual.loc[new_index]}\n")


df_err = calculate_error(df_actual, df_pred)
#print(f"error:\n {df_err.loc[new_index]}\n")

summary= get_high_error_timestamps(df_err)

index_list = summary.index.tolist()
inspect_sequences(df_actual, df_pred, index_list)
#-----PLOT DATA---------
def plot_features():

    cols_per_fig = df.shape[0]/2
    total_cols = df.shape[1]

    for i in range(0, total_cols, cols_per_fig):
        chunk = df[df.columns[i:i+cols_per_fig]]
        ncols = 10
        nrows = math.ceil(chunk.shape[1] / ncols)

        axes = chunk.plot(subplots=True, layout=(nrows, ncols), figsize=(24*2, nrows*4))

        axes = np.array(axes).flatten() if isinstance(axes, (np.ndarray, list)) else [axes]

        plt.suptitle(f"Columns {i+1} to {i+chunk.shape[1]}", fontsize=20)
        plt.tight_layout(rect=[0, 0, 1, 0.95])

        # Save figure
        filename = f"ml/features_{vm}_{i+1}_to_{i+chunk.shape[1]}.png"
        plt.savefig(filename, dpi=300)
        plt.close()


def plot_err_vs_t(df_error):
    #error over time
    plt.figure()
    plt.plot(df_error.index, df_pred['error_total'], color='c')
    plt.title("Pred Error Over Time")
    plt.xticks(rotation=45)
    plt.savefig(f"ml/error_over_time_{vm}.png")
    plt.close()

def plot_act_and_pred_vals(df_actual, df_pred):
    selected_cols = df_actual.columns[:]

    #Actual
    ax = df_actual[selected_cols].plot(subplots=True, figsize=(12,32))
    fig = ax[0].get_figure()
    fig.savefig(f"ml/actual_vals_{vm}.png", dpi=300, bbox_inches='tight')

    #Predicted
    ax = df_pred[selected_cols].plot(subplots=True, figsize=(12,32))
    fig = ax[0].get_figure()
    fig.savefig(f"ml/predicted_vals_{vm}.png", dpi=300, bbox_inches='tight')
    return "plots created"

#print(plot_act_and_pred_vals(df_actual, df_pred))
