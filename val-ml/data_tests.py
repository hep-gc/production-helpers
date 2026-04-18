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
from scipy.stats import ks_2samp
from statsmodels.tsa.stattools import adfuller
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


#---------- VARIABLES ----------
csv = 'raw_year_features_belle.csv'

#LOAD DATA
def load_data(csv):
    return pd.read_csv(csv, index_col="Datetime", parse_dates=True)

#CLEAN DATA
def clean_data(df):
    df = np.log1p(df)
    low_var_cols = df.columns[df.std() < 0.01]
    print(low_var_cols)
    df = df.drop(columns=low_var_cols)
    return df
    

# 1. STATIONARITY (ADF TEST)
def stationarity_test(df):
    results = {}
    for col in df.columns:
        series = df[col].dropna()
        if len(series) < 20:
            continue

        stat, p_value, _, _, _, _ = adfuller(series)

        results[col] = {
            "adf_stat": stat,
            "p_value": p_value,
            "is_stationary(p<0.05)": p_value < 0.05
        }

    return pd.DataFrame(results).T


# 2. AUTOCORRELATION STRENGTH
def autocorr_score(df, max_lag=20):
    scores = {}

    for col in df.columns:
        series = df[col].dropna().values
        if len(series) < max_lag + 1:
            continue

        series = (series - np.mean(series)) / (np.std(series) + 1e-8)

        acfs = []
        for lag in range(1, max_lag + 1):
            acf = np.corrcoef(series[:-lag], series[lag:])[0, 1]
            acfs.append(abs(acf))

        scores[col] = np.mean(acfs)

    return pd.DataFrame.from_dict(scores, orient="index", columns=["mean_abs_autocorr"])


# 3. FEATURE CORRELATION STABILITY
def correlation_matrix(df):
    return df.corr()


# 4. DISTRIBUTION SHIFT (KS TEST)
def distribution_shift(df):
    split = int(len(df) * 0.5)

    early = df.iloc[:split]
    late = df.iloc[split:]

    results = {}

    for col in df.columns:
        stat, p = ks_2samp(early[col], late[col])
        results[col] = {
            "ks_stat": stat,
            "p_value": p,
            "distribution_shift": p < 0.05
        }

    return pd.DataFrame(results).T


# 5. REGIME DRIFT (ROLLING STATISTICS CHANGE)
def regime_drift(df, window=50):
    drift_scores = {}

    for col in df.columns:
        rolling_mean = df[col].rolling(window).mean()
        rolling_std = df[col].rolling(window).std()

        drift_mean = np.nanstd(rolling_mean)
        drift_std = np.nanstd(rolling_std)

        drift_scores[col] = drift_mean + drift_std

    return pd.DataFrame.from_dict(drift_scores, orient="index", columns=["regime_drift_score"])


# 6. SEASONALITY / FREQUENCY SIGNAL (FFT ENERGY PEAK)
def seasonality_score(df):
    scores = {}

    for col in df.columns:
        series = df[col].dropna().values
        if len(series) < 10:
            continue

        series = series - np.mean(series)

        fft = np.fft.fft(series)
        power = np.abs(fft) ** 2

        # ignore zero freq
        peak_power = np.max(power[1:])
        total_power = np.sum(power[1:]) + 1e-8

        scores[col] = peak_power / total_power

    return pd.DataFrame.from_dict(scores, orient="index", columns=["seasonality_strength"])


# 7. SIMPLE "LEARNABILITY" SCORE VIA PCA RECONSTRUCTION
def reconstruction_learnability(df):
    scaler = StandardScaler()
    X = scaler.fit_transform(df.values)

    pca = PCA(n_components=min(5, df.shape[1]))
    X_pca = pca.fit_transform(X)
    X_recon = pca.inverse_transform(X_pca)

    error = np.mean((X - X_recon) ** 2, axis=0)

    return pd.DataFrame({
        "feature_reconstruction_error": error
    }, index=df.columns)


# RUN ALL
def run_diagnostics(df):

    print("\n=== STATIONARITY (ADF) ===")
    print(stationarity_test(df))

    print("\n=== AUTOCORRELATION ===")
    print(autocorr_score(df))

    print("\n=== DISTRIBUTION SHIFT (KS TEST) ===")
    print(distribution_shift(df))

    print("\n=== REGIME DRIFT ===")
    print(regime_drift(df))

    print("\n=== SEASONALITY ===")
    print(seasonality_score(df))

    print("\n=== PCA RECONSTRUCTION (LEARNABILITY) ===")
    print(reconstruction_learnability(df))


if __name__ == "__main__":
    import sys
    df= load_data(csv)
    df = df.drop(columns=['pkts_in','pkts_out','enclosure pool IOPS read','enclosure pool IOPS write','storage pool IOPS write','storage pool IOPS read'])
    df = clean_data(df)

    run_diagnostics(df)
