# Tools for Anomaly Detection

## Install Requirements
```
python3 -m pip install -r requirements.txt
```

## Scripts

### `ganglia_request.py`
Contains the `GangliaAPI` module for getting data from Ganglia server running the [request api](https://github.com/hep-gc/production-helpers/tree/monitoring-tools/ganglia/api).

### `process_data.py`
Contains the `Data` module for requesting and processing data using `GangliaAPI`.

### `utilities.py`
Contains auxillary functions for io, hashing, and sending emails.

### `run_analysis.py`
```
USAGE: run_analysis.py [config_file]
```
Script for running anomaly detection. If any anomalies are detected, an email with an anomaly report will be sent to the contact email defined in the configuration file. If a config file is not specified, the script will attempt to use `config.txt` by default. An example configuration file is provided (`example.txt`).

## Anomaly detection overview

This implementation of anomaly detection is heavily based on [this paper](https://www.epj-conferences.org/articles/epjconf/abs/2021/05/epjconf_chep2021_02011/epjconf_chep2021_02011.html). For each host defined in the `[manifest]` section of the configuration file, the script will request one week of training data (data from one week ago to just before today's date unless [otherwise specified](#specifying-custom-training-intervals)) from the server specified in the `[config]` section and train the [specified model](#compatible-models) on this data.  

Data is mean-aggregated every 10 minutes, thus each day has 144 data points per day per host per metric. Training data is then split into 8-hour multivariate windows every starting at each datapoint and normalized to form the training data set.  

Next, the script will use the trained model to do a prediction on the current day. Since a new window opens every 8 hours, the script will automatically predict on as many windows as are currently available. Trained models are cached, so it can be run as a cron job 1-3 times a day. If anomalies are detected, it will create a plot for the affected host and send it along with a report to the given email address.

### Compatible models

Currently the `IForest` detector from the [pyod](https://pyod.readthedocs.io/en/latest/) module and `AELstmTF2` from [adcern](https://gitlab.cern.ch/cloud-infrastructure/data-analytics/-/tree/master/adcern) arei explicitly supported. However, any model based on the `BaseDetector` class from PyOD can be made to work.

### Specifying custom training intervals

After the `Metrics` column in the `[manifest]` section of the configuration file, you may add an additional two columns. The first is a unix timestamp that denotes the end of the training interval and the second is the start of the interval. For example, a training period of 2 weeks ending on the 11th of november can be specified as 
```
# Cluster	Hostname				Metrics					Train-end-date	Look-behind
cluster		host.domain.ca	metric1,metric2	1636617600			e-2wk
```
More information on specifying times can be found [here](https://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html#AT-STYLE_TIME_SPECIFICATION).
