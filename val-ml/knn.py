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
from sklearn.neighbors import NearestNeighbors

#to display all columns or rows
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

#---------- Variables ----------
csv = 'raw_year_features_belle.csv'
k = 5
match = re.search(r"raw_year_features_(.+)\.csv", csv)

if match:
    vm = match.group(1)
#-------------------------------

#load data
def load_data(csv):
    return pd.read_csv(csv, index_col="Datetime", parse_dates=True)

#clean data
def clean_data(df):
    df = np.log1p(df)
    low_var_cols = df.columns[df.std() < 0.007]
    print(low_var_cols)
    df = df.drop(columns=low_var_cols)
    return df
    
def get_change(df, stds):
    return df

def plot_features(df):

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
        filename = f"ml/features_{vm}_{i+1}_to_{i+chunk.shape[1]-1}.png"
        plt.savefig(filename, dpi=300)
        print(f"plot {filename} saved")
        plt.close()

def plot_single_column(df, column, end_index):
    # subset the datta
    df_plot = df.loc[:end_index, column]

    # Plot
    plt.figure(figsize=(16, 6))
    plt.scatter(df_plot.index, df_plot.values, color='c')
    plt.title(f"{column} up to index {end_index}", fontsize=16)
    plt.grid(True)
    plt.tight_layout()

    # Save figure
    filename = f"ml/plot_{column}_{end_index}.png"
    plt.savefig(filename, dpi=300)
    print(f"Plot saved: {filename}")
    plt.close()


#plot_features(df)
#plot_single_column(df, 'storage pool read BW', "2025-09-17")

#----PREPARE DATA------
df= load_data(csv)
df = df.drop(columns=['storage free size','storage refer size','enclosure free size','storage-RDC refer size','load_five','load_fifteen','enclosure refer size','Unknown_SSH_Connections','pkts_in','pkts_out','enclosure pool IOPS read','enclosure pool IOPS write','storage pool IOPS write','storage pool IOPS read','storage-RDC free size'])

df = clean_data(df)

# Split
df_test = df['2026-01-21':]
df_train  = df[:'2026-01-20']

print("OVERVIEW  DATAFRAME:\n")
print(df.describe().transpose())
print("\n")


#scale Min-Max
# Get max from train
train_max = df_train.max()

#print(f"train max: {train_max}\n")
# Scale train and test to 0-1 using training statistics
df_train_scaled = (df_train) / train_max
df_test_scaled = (df_test) / train_max

#df_train_scaled = df_train
#df_test_scaled = df_test


#print("OVERVIEW TRAIN AND TEST DATAFRAME:\n")
#print("train\n")
#print(df_train.describe().transpose())
#print("\n")
#print("test\n")
#print(df_test.describe().transpose())
#print("\n")

print("Train stats:", df_train_scaled.values.min(), df_train_scaled.values.max())
print("Test stats:", df_test_scaled.values.min(), df_test_scaled.values.max())

#---------------KNN---------------------------
# --- kNN ---
nbrs = NearestNeighbors(n_neighbors=k)
nbrs.fit(df_train_scaled)

distances, indices = nbrs.kneighbors(df_train_scaled)

scores = distances[:, -1]

# --- threshold ---
threshold = scores.mean() + 3 * scores.std()
labels = np.where(scores > threshold, -1, 1)

num_anomalies = np.sum(labels == -1)
print("Num anomalies:", num_anomalies)

# --- store results ---
df_train = df_train.copy()
df_train["anomaly_score"] = scores
df_train["anomaly_label"] = labels

most_anomalous = df_train.sort_values("anomaly_score", ascending=False)

print("\nTop anomalies:")
print(most_anomalous.head(20))

print("\nLabel distribution:")
print(df_train["anomaly_label"].value_counts())


X = df_train_scaled.values
kth_neighbor_idx = indices[:, -1]

anomaly_indices = np.where(labels == -1)[0]

print("\nTop contributing features PER anomaly:\n")

for idx in anomaly_indices[:10]:
    
    timestamp = df_train.index[idx]
    neighbor_timestamp = df_train.index[kth_neighbor_idx[idx]]
    
    diff = X[idx] - X[kth_neighbor_idx[idx]]
    contrib = diff ** 2
    
    contrib_df = pd.DataFrame({
        "feature": df_train.columns[:-2],
        "contribution": contrib
    }).sort_values("contribution", ascending=False)
    
    print(f"\n--- Anomaly at timestamp: {timestamp} ---")
    print(f"Nearest neighbor timestamp: {neighbor_timestamp}")
    print(contrib_df.head(5))



