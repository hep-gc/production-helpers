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
#-------------------------------------------------
#host path
host_path = r"rrds/Belle-II RDC/xrd5.belle.uvic.ca/"

#resolution
res = YEAR

#------------------------------------------------
#------------------------------------------------
dfs = []
starts = []
ends = []

#get data timeframe
for file in os.listdir(host_path):
    file_path = os.path.join(host_path, file)
    info = rrdtool.info(file_path)
    starts.append(rrdtool.first([file_path, "--rraindex", res]))
    ends.append(rrdtool.last(file_path))

start_time = max(starts)
end_time = max(ends)
print(f"chosen start: {datetime.datetime.fromtimestamp(start_time)}")
print(f"chosen end: {datetime.datetime.fromtimestamp(end_time)}")

#trues = []
#import data from each file in host
for file in os.listdir(host_path):
    file_path = os.path.join(host_path, file)
    #import data
    fetch_data = rrdtool.fetch(file_path, ["AVERAGE","--start", str(start_time), "--end", str(end_time), "--resolution", "600"])

    (start_t, end_t, step) = fetch_data[0]
    rows = fetch_data[2]
    #print(f"file name {file_path}, Step: {step}")

    #get values
    metric_name = file.replace(".rrd", "")
    values = [r[0] if r[0] is not None else np.nan for r in rows]
    timestamps = list(range(start_t, start_t + step*len(values), step))

    df_metric = pd.DataFrame({
        "Datetime": pd.to_datetime(timestamps, unit="s"),
        metric_name: values
    })

    df_metric = df_metric.set_index("Datetime")

    dfs.append(df_metric)

    #print(f"{metric_name} step: {step}")


#----CREATE DATAFRAME----

#for visualization
pd.set_option('display.max_rows', None)

# merge all metrics
df = pd.concat(dfs, axis=1)
df.index.name = "Datetime"
df.index = pd.to_datetime(df.index)
df = df.sort_index()
df = df.asfreq("600s")

#drop rows and columns where all values are missing
df = df.dropna(how="all")
df = df.dropna(axis=1, how='all')

#columns and rows with some missing values
missing_per_column = df.isna().sum()
print(missing_per_column[missing_per_column > 0])

missing_per_row = df.isna().sum(axis=1)
print(missing_per_row[missing_per_row > 0])

df = df.dropna() 


print(f"any value missing? {df.isna().any().any()}")
print(f"total missing vals: {df.isna().sum().sum()}")

#check dataframe in order
print(df.index.is_monotonic_increasing)
print(df.head(50))

#get rid of unknown ssh connections, boottime, storage refer size, compress ratio, part max use
df = df.drop(columns=['boottime', 'part_max_used'])
#df = df.drop(columns=['Unknown_SSH_Connections', 'boottime', 'storage refer size', 'storage-RDC compress ratio', 'part_max_used'])

print(df.head(50))
#save into csv
df.to_csv("raw_year_features_belle.csv")

exit()

