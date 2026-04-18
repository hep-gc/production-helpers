import pandas as pd
import rrdtool
import os
import csv
import numpy as np
import datetime

YEAR = "2"
BIWEEK = "1"
DAY = "0"

#-------------------VARIABLES---------------------
#path to vm
host_path = r"rrds/Belle-II RDC/xrd5.belle.uvic.ca/"
#resolution of timestamps
res = YEAR
#path to saved csv
save_path = "raw_year_features_belle.csv"
#features to ignore
del_features = ['boottime', 'part_max_used']
#-------------------------------------------------


# 1. TIMEFRAME EXTRACTION
def get_timeframe(host_path, res):
    """
    Computes the global start and end timestamps across all RRD files.

    Args:
        host_path (str): Path to directory containing RRD files.
        res (str): RRA index resolution selector.

    Returns:
        tuple: (start_time, end_time)
    """
    starts = []
    ends = []

    for file in os.listdir(host_path):
        file_path = os.path.join(host_path, file)

        starts.append(rrdtool.first([file_path, "--rraindex", res]))
        ends.append(rrdtool.last(file_path))

    start_time = max(starts)
    end_time = max(ends)

    print(f"chosen start: {datetime.datetime.fromtimestamp(start_time)}")
    print(f"chosen end: {datetime.datetime.fromtimestamp(end_time)}")

    return start_time, end_time


# 2. DATA LOADING FROM RRD FILES
def load_rrd_data(host_path, start_time, end_time):
    """
    Loads time series data from all RRD files in a directory.

    Args:
        host_path (str): Path to RRD files.
        start_time (int): Global start timestamp.
        end_time (int): Global end timestamp.

    Returns:
        list: List of pandas DataFrames (one per metric).
    """
    dfs = []

    for file in os.listdir(host_path):
        file_path = os.path.join(host_path, file)

        fetch_data = rrdtool.fetch(
            file_path,
            ["AVERAGE", "--start", str(start_time), "--end", str(end_time), "--resolution", "600"]
        )

        (start_t, end_t, step) = fetch_data[0]
        rows = fetch_data[2]

        metric_name = file.replace(".rrd", "")

        values = [r[0] if r[0] is not None else np.nan for r in rows]
        timestamps = list(range(start_t, start_t + step * len(values), step))

        df_metric = pd.DataFrame({
            "Datetime": pd.to_datetime(timestamps, unit="s"),
            metric_name: values
        })

        df_metric = df_metric.set_index("Datetime")

        dfs.append(df_metric)

    return dfs


# 3. DATAFRAME CREATION + CLEANING
def build_and_clean_dataframe(dfs):
    """
    Merges, cleans, and prepares the final dataset.

    Args:
        dfs (list): List of DataFrames per metric.

    Returns:
        pd.DataFrame: Cleaned final dataset.
    """
    pd.set_option('display.max_rows', None)

    df = pd.concat(dfs, axis=1)
    df.index.name = "Datetime"
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.asfreq("600s")

    # drop empty rows/columns
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how='all')

    # remove remaining missing values
    df = df.dropna()

    print(f"any value missing? {df.isna().any().any()}")
    print(f"total missing vals: {df.isna().sum().sum()}")

    print(df.index.is_monotonic_increasing)
    print(df.head(50))

    # drop unwanted features
    df = df.drop(columns=del_features)

    print(df.head(50))

    return df


# MAIN
def main():
    start_time, end_time = get_timeframe(host_path, res)

    dfs = load_rrd_data(host_path, start_time, end_time)

    df = build_and_clean_dataframe(dfs)

    df.to_csv(save_path)


if __name__ == "__main__":
    main()
























