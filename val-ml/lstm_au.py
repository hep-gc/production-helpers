import re
import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.utils.data as data
import torch.optim as optim
import math

#---------- VARIABLES ----------
#input dataset
csv = 'raw_year_features_belle.csv'

#path to save plots
fig_path = 'ml'


lookback = 1 #sequence lenght for LSTM input

#model hyperparameters
layers = 1
hidden_s = 100 #hidden state
latent_s= 50 #latent state

#training epochs
n_epochs = 75
#--------------------------------

#to display all columns or rows
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


#load data
def load_data(csv):
    """
    Load dataset from CSV file.

    Args:
        csv (str): Path to CSV file.

    Returns:
        pd.DataFrame: DataFrame indexed by Datetime.
    """
    return pd.read_csv(csv, index_col="Datetime", parse_dates=True)

#clean data
def clean_data(df):
    """
    Apply preprocessing:
    - Log transformation
    - Remove low-variance features

    Args:
        df (pd.DataFrame): Raw dataset.

    Returns:
        pd.DataFrame: Cleaned dataset.
    """
    df = np.log1p(df)
    low_var_cols = df.columns[df.std() < 0.01]
    print(low_var_cols)
    df = df.drop(columns=low_var_cols)
    return df
    

def plot_features(df):
    """
    Plot all features as scatter plots over time

    Args:
        df (pd.DataFrame): Input dataset.
    """
    cols_per_fig = int(df.shape[0]/2)
    total_cols = int(df.shape[1])

    for i in range(0, total_cols, cols_per_fig):
        chunk = df[df.columns[i:i+cols_per_fig]].copy()
        chunk.reset_index(inplace=True) 

        ncols = 10
        nrows = math.ceil(chunk.shape[1] / ncols)

        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(24*2, nrows*4))
        axes = np.array(axes).flatten() 

        for j, col in enumerate(chunk.columns[1:]):
            chunk.plot(kind='scatter', x=chunk.columns[0], y=col, ax=axes[j], color='c')
            axes[j].set_title(col)

        for k in range(len(chunk.columns[1:]), len(axes)):
            axes[k].set_visible(False)

        plt.suptitle(f"Columns {i+1} to {i+chunk.shape[1]-1}", fontsize=20)
        plt.tight_layout(rect=[0, 0, 1, 0.95])

        # Save figure
        filename = f"{fig_path}/features_{i+1}_to_{i+chunk.shape[1]-1}.png"
        plt.savefig(filename, dpi=300)
        print(f"plot {filename} saved")
        plt.close()

def plot_single_column(df, column, end_index):
    """
    Plot a single feature up to a specific timestamp.

    Args:
        df (pd.DataFrame): Input dataset.
        column (str): Feature name.
        end_index: Timestamp limit.
    """
    df_plot = df.loc[:end_index, column]

    # Plot
    plt.figure(figsize=(16, 6))
    plt.scatter(df_plot.index, df_plot.values, color='c')
    plt.title(f"{column} up to index {end_index}", fontsize=16)
    plt.grid(True)
    plt.tight_layout()

    # Save figure
    filename = f"{fig_path}/plot_{column}_{end_index}.png"
    plt.savefig(filename, dpi=300)
    print(f"Plot saved: {filename}")
    plt.close()

#---------------------PREPARE DATA---------------------------
# Load data
df = load_data(csv)

# Drop manually selected noisy/irrelevant features
df = df.drop(columns=[
    'pkts_in','pkts_out',
    'enclosure pool IOPS read','enclosure pool IOPS write',
    'storage pool IOPS write','storage pool IOPS read',
    'storage-RDC used size','storage used size',
    'enclosure used size','enclosure refer size',
    'disk_free','disk_total','mem_total',
    'load_fifteen','load_five','storage-RDC refer size'
])

# Clean data
df = clean_data(df)

print("OVERVIEW LOG TRANSFORM DATAFRAME:\n")
print(df.describe().transpose())
print("\n")


# Split
df_test = df['2026-01-16':]
df_train  = df[:'2026-01-15']


#scaling
train_max = df_train.max()

#scaling disabled left for experimentation
#df_train_scaled = (df_train) / train_max
#df_test_scaled = (df_test) / train_max

df_train_scaled = df_train
df_test_scaled = df_test


print("OVERVIEW TRAIN AND TEST DATAFRAME:\n")
print("train\n")
print(df_train.describe().transpose())
print("\n")
print("test\n")
print(df_test.describe().transpose())
print("\n")


print("Train stats:", df_train_scaled.values.min(), df_train_scaled.values.max())
print("Test stats:", df_test_scaled.values.min(), df_test_scaled.values.max())

#----CREATE WINDONW SIZE -----------

#convert dataframe into list of sequences
features = df.shape[1]

def create_window(dataset, lookback):
    """
    Convert time series into sequences for LSTM input.

    Args:
        dataset (np.array): Input data.
        lookback (int): Number of timesteps per sequence.

    Returns:
        tuple: (input_sequences, targets)
    """
    x, y = [], []
    for i in range(len(dataset)-lookback):
        x.append(dataset[i:i+lookback])
        y.append(dataset[i+lookback])
    return torch.tensor(np.array(x), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

#create train/test dataset sequences
x_train, _ = create_window(df_train_scaled.values, lookback)
x_test, _  = create_window(df_test_scaled.values, lookback)

# Autoencoder uses target = input
train_dataset = data.TensorDataset(x_train, x_train)
test_dataset  = data.TensorDataset(x_test, x_test)

#size, lookback, features
print(x_train.shape)
print(x_test.shape)

#-------CREATE MODEL------------
class Autoencoder(nn.Module):
    def __init__(self, seq_len=lookback, n_features=features, hidden_size=hidden_s, latent_size=latent_s,
                 num_layers=layers, dropout=0.0, bidirectional=False):
        super().__init__()

        self.seq_len = seq_len
        self.hidden_size = hidden_size
        self.latent_size = latent_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional

        encoder_output_size = hidden_size * (2 if bidirectional else 1)

        # Encoder
        self.encoder_lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
            bidirectional=bidirectional
        )

        # Bottleneck
        self.encoder_linear = nn.Linear(
            encoder_output_size,
            latent_size
        )

        # Decoder
        self.decoder_lstm = nn.LSTM(
            input_size=latent_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        # Final reconstruction layer
        self.decoder_linear = nn.Linear(hidden_size, n_features)

    def forward(self, x):
        # x shape: (batch_size, seq_len, n_features)

        _, (hidden, _) = self.encoder_lstm(x)

        # Take final hidden state
        if self.bidirectional:
            hidden_forward = hidden[-2]
            hidden_backward = hidden[-1]
            hidden_final = torch.cat((hidden_forward, hidden_backward), dim=1)
        else:
            hidden_final = hidden[-1]

        # Latent representation
        latent = self.encoder_linear(hidden_final)

        # Repeat latent vector across sequence length
        repeated_latent = latent.unsqueeze(1).repeat(1, self.seq_len, 1)

        # Decode sequence
        decoded, _ = self.decoder_lstm(repeated_latent)

        # Reconstruct original features
        reconstructed = self.decoder_linear(decoded)

        return reconstructed



#---------TRAINING--------------------------
model=Autoencoder()
optimizer = optim.Adam(model.parameters())
loss_fn = nn.MSELoss() #loss function
loader = data.DataLoader(train_dataset, batch_size=60, shuffle=True)


for epoch in range(n_epochs):
    model.train()
    for x_batch, _ in loader:
        y_pred = model(x_batch)
        loss = loss_fn(y_pred, x_batch)

        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    #evaluation
    model.eval()
    with torch.no_grad():
        recon_train = model(x_train)
        recon_test = model(x_test)
        train_rmse = torch.sqrt(loss_fn(recon_train, x_train))
        test_rmse = torch.sqrt(loss_fn(recon_test, x_test))

    print(
        f"Epoch {epoch}: "
        f"train RMSE {train_rmse.item():.7f} | "
        f"test RMSE {test_rmse.item():.7f}"
    )


#----VISUALIZE RESULTS-------------
def get_recons(df):
    """
    Generate reconstructed sequences from trained model.

    Args:
        df (pd.DataFrame): Input dataset

    Returns:
        tuple:
            df_recon (pd.DataFrame): Reconstructed values
            df_actual (pd.DataFrame): Actual values
    """

    seqs, _ = create_window(df.values, lookback)
    with torch.no_grad():
        recon = model(seqs)
    recon = recon.numpy()
    recon = recon[:, -1, :]

    df_recon = pd.DataFrame(recon, index=df.index[lookback:], columns=df.columns)
    df_actual = df[lookback:]

    return df_recon, df_actual


def get_error(df_recon, df_actual):
    """
    Compute reconstruction error per feature and total error.

    Args:
        df_recon (pd.DataFrame): Reconstructed values from the model.
        df_actual (pd.DataFrame): actual values.

    Returns:
        pd.DataFrame: DataFrame containing squared error per feature and
                      an additional column 'error_total' representing
                      overall reconstruction error per timestamp.
    """
    df_error = pd.DataFrame((df_actual-df_recon)**2, columns=df_actual.columns, index=df_actual.index) #relative error
    df_error['error_total']= np.sqrt(df_error.mean(axis=1))
    return df_error

def get_high_error_timestamps(df_error, top_n=50):
    """
    Identify timestamps with the highest reconstruction error.

    Args:
        df_error (pd.DataFrame): DataFrame containing per-feature errors
                                 and 'error_total'.
        top_n (int, optional): Number of anomalous timestamps to display.
                               Default is 50.

    Returns:
        pd.DataFrame: Summary DataFrame sorted by highest total error,
                      including:
                      - max_feature: feature contributing most to error
                      - max_feature_error: its error value
                      - error_total: total reconstruction error
    """
    # Separate feature errors from total error
    df_features = df_error.drop(columns=['error_total'])
    max_feature = df_features.idxmax(axis=1)
    max_value = df_features.max(axis=1)
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
    #print(summary.head(top_n))
    return summary

def inspect_sequences(df_actual, df_recon, index_list):
    """
    Inspect and compare actual vs reconstructed values for selected timestamps.

    Args:
        df_actual (pd.DataFrame): actual values.
        df_recon (pd.DataFrame): Reconstructed values.
        index_list (list): List of timestamps to inspect.

    Returns:
        None
    """
    #df_recon = np.expm1(df_recon)
    #df_actual = np.expm1(df_actual)
    #df_recon = df_recon*train_max
    #df_actual = df_actual*train_max
    count = 0
    for index in index_list:
        data = {'actual': df_actual.loc[index], 'recon': df_recon.loc[index]}
        df = pd.DataFrame(data, index=df_actual.columns)
        if count <10:
            print(f"\n{index}\n")
            print(df.head(40))
        count = count+1


#Run analysis
df_recon, df_actual = get_recons(df_train_scaled)
df_error = get_error(df_recon, df_actual)
summary = get_high_error_timestamps(df_error)
index_list = summary.index.tolist()
inspect_sequences(df_actual, df_recon, index_list)

