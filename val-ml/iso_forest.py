import pandas as pd
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.ensemble import IsolationForest
from sklearn.inspection import DecisionBoundaryDisplay
from sklearn.preprocessing import StandardScaler
import math

df = pd.read_csv('raw_yearly_metrics.csv', index_col="Datetime", parse_dates=True)

#for visualization
pd.set_option('display.max_rows', None)
#pd.set_option('display.max_columns', None)

# Drop features with zero variance
df = df.loc[:, df.std() > 0]

#-----------------------------------
#df = df['2026-01-01':'2026-02-10']


#visualize
#print(df.shape)
#print(df.sample(50))

"""
#--- PLOT DATA ----

#PLOT 200 FEATURES
cols_per_fig = 100
total_cols = df.shape[1]
# Loop through in chunks
for i in range(0, total_cols, cols_per_fig):
    chunk = df[df.columns[i:i+cols_per_fig]]
    ncols = 10
    nrows = math.ceil(chunk.shape[1] / ncols)
    
    axes = chunk.plot(subplots=True, layout=(nrows, ncols), figsize=(24*2, nrows*4))
    
    plt.suptitle(f"Columns {i+1} to {i+chunk.shape[1]}", fontsize=20)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save figure
    filename = f"ml/anomalous_plot_columns_{i+1}_to_{i+chunk.shape[1]}.png"
    plt.savefig(filename, dpi=300)
    plt.close()  # close the figure to free memory
"""

#------PREPARE DATA---------
train_frac = 0.8
test_frac = 0.2
n_rows = len(df)
n_test = int(n_rows * test_frac)

# Split
df_test_b1 = df[:'2025-06-01']
df_test_b2 = df['2025-12-01':]
df_train  = df['2025-06-01':'2025-12-01']

"""
#visualize data
cols_per_fig = 100
total_cols = df_train.shape[1]
# Loop through in chunks
for i in range(0, total_cols, cols_per_fig):
    chunk = df_train[df_train.columns[i:i+cols_per_fig]] 
    ncols = 10
    nrows = math.ceil(chunk.shape[1] / ncols)
    
    axes = chunk.plot(subplots=True, layout=(nrows, ncols), figsize=(24*2, nrows*4))
    
    axes = np.array(axes).flatten() if isinstance(axes, (np.ndarray, list)) else [axes]
    
    plt.suptitle(f"Columns {i+1} to {i+chunk.shape[1]}", fontsize=20)
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    
    # Save figure
    filename = f"ml/plot_train_columns_{i+1}_to_{i+chunk.shape[1]}.png"
    plt.savefig(filename, dpi=300)
    plt.close()
"""
#scale values
scaler = StandardScaler()

df_train_scaled = scaler.fit_transform(df_train.values)
df_test_b1_sc = scaler.transform(df_test_b1.values)
df_test_b2_sc = scaler.transform(df_test_b2.values)

#-----TRAIN ISOLATION FOREST-----
clf = IsolationForest(max_samples=100, random_state=0, max_features=50)
clf.fit(df_train_scaled)

#-----TEST---------

# predict on test data
df_test_b1['anomaly'] = clf.predict(df_test_b1_sc)
df_test_b2['anomaly'] = clf.predict(df_test_b2_sc)

#save scores
df_test_b1['score'] = clf.decision_function(df_test_b1_sc)
df_test_b2['score'] = clf.decision_function(df_test_b2_sc)

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

#count anomalies and get percentage
num_anomalies = (df_test_b1['anomaly'] == -1).sum()
print("Number of anomalies b1 detected:", num_anomalies)

percentage = (num_anomalies / len(df_test_b1)) * 100
print(f"Percentage of anomalies in test set 1: {percentage:.2f}%")

num_anomalies = (df_test_b2['anomaly'] == -1).sum()
print("Number of anomalies b1 detected:", num_anomalies)

percentage = (num_anomalies / len(df_test_b2)) * 100
print(f"Percentage of anomalies in test set 2: {percentage:.2f}%")
#--------PLOT---------

plt.figure(figsize=(16,6))

# anomalies
anomaly_idx = df_test_b1['anomaly'] == -1
plt.scatter(
    df_test_b1.index[anomaly_idx],
    df_test_b1['score'][anomaly_idx],
    color='red',
    s=15,
    label='anomaly'
)

# score line
plt.plot(df_test_b1.index, df_test_b1['score'], label='score', color='blue')

plt.title("Anomaly Score b1 vs Time")
plt.legend()
plt.tight_layout()
plt.savefig("ml/anomaly_score_test_b1.png", dpi=300)
plt.close()

plt.figure(figsize=(16,6))

# anomalies
anomaly_idx = df_test_b2['anomaly'] == -1
plt.scatter(
    df_test_b2.index[anomaly_idx],
    df_test_b2['score'][anomaly_idx],
    color='red',
    s=15,
    label='anomaly'
)

# score line
plt.plot(df_test_b2.index, df_test_b2['score'], label='score', color='blue')

plt.title("Anomaly Score b2 vs Time")
plt.legend()
plt.tight_layout()
plt.savefig("ml/anomaly_score_test_b2.png", dpi=300)
plt.close()
