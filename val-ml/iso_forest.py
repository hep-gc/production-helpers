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
from sklearn.ensemble import IsolationForest

#----------VARIABLES----------
# Path to input CSV file
csv = 'raw_year_features_belle.csv'

#path to save plots
fig_path = 'ml'
#-------------------------------
# Configure pandas to display full DataFrame (no truncation)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

match = re.search(r"raw_year_features_(.+)\.csv", csv)
if match:
    vm = match.group(1)

#load data
def load_data(csv):
    """
    Load dataset from CSV file.

    Args:
        csv (str): Path to CSV file.

    Returns:
        pd.DataFrame: DataFrame
    """
    return pd.read_csv(csv, index_col="Datetime", parse_dates=True)

#clean data
def clean_data(df):
    """
    Apply preprocessing steps:
    - Log transformation
    - Remove low-variance features (near-constant signals)

    Args:
        df (pd.DataFrame): Raw input DataFrame.

    Returns:
        pd.DataFrame: Cleaned DataFrame.
    """
    df = np.log1p(df)
    low_var_cols = df.columns[df.std() < 0.007] #can change treshold to include more/less features
    #print(low_var_cols)
    df = df.drop(columns=low_var_cols)
    return df
    

def plot_features(df):
    """
    Generate scatter plots for all features over time.

    Args:
        df (pd.DataFrame): Input DataFrame.
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
        filename = f"{fig_path}/features_{vm}_{i+1}_to_{i+chunk.shape[1]-1}.png"
        plt.savefig(filename, dpi=300)
        print(f"plot {filename} saved")
        plt.close()

def plot_single_column(df, column, end_index):
    """
    Plot a single feature over time up to a given index.

    Args:
        df (pd.DataFrame): Input DataFrame.
        column (str): Column name to plot.
        end_index (str or datetime): Upper bound for slicing.
    """
    # subset the datta
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

#==========================================================
#PREPARE DATA
df= load_data(csv)
#drop manually selected features
df = df.drop(columns=['Unknown_SSH_Connections','pkts_in','pkts_out','enclosure pool IOPS read','enclosure pool IOPS write','storage pool IOPS write','storage pool IOPS read','storage-RDC used size','storage used size','enclosure used size', 'enclosure refer size','disk_free', 'disk_total','mem_total','load_fifteen', 'load_five', 'storage-RDC refer size'])
df = clean_data(df)

print("OVERVIEW DATAFRAME:\n")
print(df.describe().transpose())
print("\n")

# Split dataset based on date
df_test = df['2026-01-21':] 
df_train  = df[:'2026-01-20']

#scale
train_max = df_train.max()

# Scaling
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

#==========================================
#ISOLATION FOREST 
#==========================================

iso =  IsolationForest(
        n_estimators=500, #number of trees
        max_samples='auto', #samples per tree
        max_features=14, #number of features per split
        random_state=42 #Controls the randomness of the selection of the feature and split values 
    )

#train model on training data
iso.fit(df_train_scaled)

#compute anomaly scores on test data saved them on 'anomaly_score' column
scores = iso.decision_function(df_test_scaled)
df_test_scaled['anomaly_score'] = scores

#Display results 
#print(df_test_scaled.describe().transpose())
print(df_test_scaled.sort_values('anomaly_score').head(50))
