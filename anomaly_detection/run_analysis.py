#!/usr/bin/env python3

# @AUTHOR: Victor Kamel

### IMPORTS

from utilities import Progress as progress

DEBUG=False

with progress("Importing modules"):

    from datetime import date, timedelta, datetime
    from joblib import dump, load
    
    if not DEBUG:
        import warnings
        warnings.filterwarnings("ignore", message=r"Passing", category=FutureWarning)

        import logging
        logging.getLogger('tensorflow').disabled = True

    from ganglia_request import GangliaAPI
    from process_data import Data
    from utilities import load_config, hash_objects, send_report
    
    import tensorflow as tf
    
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import concurrent.futures
    import subprocess
    import importlib
    import socket
    import sys
    import os

# Parse command line arguments
args = sys.argv
if   len(args) == 1: config_file = 'config.txt'
elif len(args) == 2: config_file = args[1]
else:
    print("USAGE: run_analysis.py [config_file]")
    exit(1)

### Define data parameters

today       = int(date.today().strftime("%s")) #  13
now         = int(datetime.today().strftime("%s"))
look_behind = 'e-1wk' # Length of training dataset - 1 wk from end
offset      = 1200    # RRDTool align to boundary correction

# Data pulled  : 1 Week (Training), 1 Day (Inference)
# Aggregated   : Every 10 Minutes (AVERAGE)
# Windows size : 48 (3 8-hours windows per day since there are 144 10min chunks per day)

# Window length, Steps to begin new window, Aggregation interval
steps, slide, resolution= 48, 1, 600

# Number of available windows
nwindows   = 3 if today < int(date.today().strftime("%s")) else (now - today) // (steps * resolution)

### Create output/cache folders
if not os.path.exists('cache') : os.makedirs('cache')
if not os.path.exists('output'): os.makedirs('output')

def save_model(model, train_data, filename):
    """
    Save anomaly detection model and normalization coefficients to a file.
    """
    det_name = model.__class__.__name__
    if   det_name == "IForest": dump((model, train_data), filename)
    elif det_name == "AELstmTF2":
        # The model (model.model_) is not serializable w/ joblib/pickle, therefore
        # it must be saved seperately from the main detector object.
        model_ = model.model_
        model_.save(filename) # Save model
        del model.model_
        dump((model, train_data), filename + "_object") # Save detector
        model.model_ = model_
        
def load_model(filename):
    """
    Load anomaly detection model and normalization coefficients to a file.
    """
    if   det_type[1]  == 'IForest'  : return load(filename)
    elif det_type[1]  == 'AELstmTF2':
        model, train_data = load(filename + "_object")
        model.model_ = tf.keras.models.load_model(filename)
        return model, train_data

def generate_plot(hostname, metrics, predictions, series, tseries):
    """
    Generate a plot for a given host with anomalous windows highlighted.
    """
    # Config
    fig, axes = plt.subplots(len(metrics), 2, figsize=(15, 8), sharey='row', sharex='col')
    fig.suptitle(f'Host: {hostname}', y=0.95)
    plt.subplots_adjust(wspace=0, hspace=0)
    
    td = datetime.fromtimestamp(today)
    colors = plt.rcParams["axes.prop_cycle"]()
    
    # Add plots to axes
    for ax, metric in zip(axes, metrics):
        c = next(colors)['color']

        for a in ax:
            a.margins(x=0)
            a.xaxis.set_tick_params(rotation=30)

        ax[0].plot(tseries.index, list(tseries[metric]), label=metric, color=c)
        ax[0].legend(loc='upper left')
        ax[0].axvspan(tseries.index[0], tseries.index[-1], alpha=0.25, color='skyblue')

        ax[1].plot(series.index, list(series[metric]), label=metric, color=c)
        
        for x in range(86400 // (steps * resolution) + 1):
            ax[1].axvline(x = td + timedelta(hours=8*x, minutes=-5), color = 'magenta', linewidth=1, alpha=0.5)
            if x < len(predictions) and predictions[x] == 1:
                ax[1].axvspan(td + timedelta(hours=8*x, minutes=-5), td + timedelta(hours=8*(x+1), minutes=-5), alpha=0.25, color='red')

    fig.legend(handles=[mpatches.Patch(color='skyblue', alpha=0.25, label='Training Period.'),
                        mpatches.Patch(color='red', alpha=0.25, label='Anomaly detected.'),
                        mpatches.Patch(edgecolor='black', alpha=0.25, label='OK.', fill=False)])
    
    # Save plot & exit
    plt.savefig(f'output/{hostname}.png', bbox_inches='tight')
    plt.close(fig)

def handle_host(host):
    """
    Gather training data for host, train model and run prediction.
    """
    
    # Silence
    if not DEBUG: sys.stdout = None
        
    global today, look_behind
    
    # Calculate hash
    hashstr = f"{host[1]}_{today}_{hash_objects(host, look_behind, offset, resolution, API, steps, slide, det_type)}"
    
    if len(host) == 5: # Allow setting a clustom training window
        today = int(host[3])
        look_behind = host[4]
        host = host[:3]
    
    # Try to load model from cache
    if hashstr in os.listdir('cache'): detector, train_data = load_model(f"cache/{hashstr}")
    else:
        # Get training data, get normalization coeffs
        train_data = Data(host, look_behind, today - offset, resolution, API, steps, slide)

        # Initialize model
        
        if det_type[1] == 'AELstmTF2':
            detector = det( 
                nr_timeseries = len(host[2]),
                nr_timesteps  = steps,
                epochs        = 3,
                verbose       = 0,
                contamination = 0.05
            )
            detector._set_n_classes(None)
        elif det_type[1] == 'IForest':
            detector = det( # IForest
                n_estimators  = 300,
                contamination = 0.05,
                verbose       = 1,
                max_samples   = 'auto', # 0.8,
                max_features  = 1.0,    # 0.8,
                random_state  = 3393
            )
        else: raise Exception(f"Unsupported detector type {det_type}")
        
        detector.fit(train_data.get_raw())               # Fit model
        save_model(detector, train_data, f"cache/{hashstr}") # Save model
    
    # Fetch inference data
    infer_data = Data(host, today - offset, f's+{8 * nwindows}h', resolution, API, steps, 48, coeffs=train_data.get_norm_coeffs())
    
    # Generate predictions
    infer = infer_data.get_raw()
    predictions = detector.predict(infer)
    
    # Generate plots if there are any anomalous hosts
    if (not DEBUG) and any(predictions): generate_plot(*host[1:3], predictions, infer_data.get_series(), train_data.get_series())
    
    return (*host[0:2], detector.predict_proba(infer), detector.decision_function(infer), predictions, detector.threshold_)

with progress("Cleaning cache"):
    # Delete cache files in the cache directory that are more than 1 day old
    for file in os.listdir('cache'):
        if "_" in file:
            ts = file.split("_")[1]
            if ts.isdigit() and (today == int(date.today().strftime("%s"))) and (int(ts) < today - (86400)): # 1 days old
                print(f"Removing {file}")
                os.unlink(f'cache/{file}')
    # Remove any plots from the ouput folder
    for file in os.listdir('output'):
        if file.endswith(".png"): os.unlink(f'output/{file}') 

with progress("Running analysis"):
    # Load config/manifest file
    config, hosts = load_config(config_file)

    API         = GangliaAPI(config['monitor_server'])
    admin_email = config['admin_email']
    
    det_type = (*config['detector'].rsplit('.', 1),)
    det      = getattr(importlib.import_module(det_type[0]), det_type[1])
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=1 if DEBUG else int(config['max_workers'])) as executor:
        res = executor.map(handle_host, hosts)

with progress("Generating report"):
    w = ["00:00:00 to 08:00:00", "08:00:00 to 16:00:00", "16:00:00 to 24:00:00"] 
    
    report = (f"Report for day: {datetime.fromtimestamp(today).date()}\n"
              f"Generated: {datetime.fromtimestamp(now)}\n"
              f"Generated by: {socket.getfqdn()}\n\n")
    
    anomalous_hosts = []
    for cluster, hostname, proba, scores, verd, thresh in res:
        report += f"HOST: {hostname}\n"
        if any(verd): anomalous_hosts.append((cluster, hostname))
        for c in range(len(verd)): report += (f"\tWindow {c} ({w[c]}):"
                                              f"  P(Outlier) = {proba[c][1] * 100:>5.1f} %"
                                              f"  Thresh = {thresh:>8.5f}"
                                              f"  Score = {scores[c]: >8.5f}"
                                              f"  Verdict: {'Anomaly Detected' if verd[c] else 'OK'}\n")

    # Send a report if any of the hosts are anomalous
    if anomalous_hosts:
        message  = "NOTICE\n\nAnomalies have been detected in the following hosts:\n"
        message += "\n\t- " + "\n\t- ".join(map(lambda host: f'{host[1]} ({API.url}?c={host[0].replace(" ", "%20")}&h={host[1]}&r=week)', anomalous_hosts))
        message += f"\n\nURL of Ganglia monitoring server: {API.url}\n\n-----\n"

        out = message + '\n' + report

        if not DEBUG:
            send_report(
                f'Anomaly report {datetime.today().strftime("%x %I:%M %p")}',
                f"Anomaly Detection System <noreply@{socket.getfqdn()}>",
                admin_email, out, anomalous_hosts)
            
            # Remove plot image files
            for host in anomalous_hosts: os.unlink(f'output/{host[1]}.png')

    else: out = "No anomalies were detected.\n\n-----\n\n" + report
    
    print(out)
    
    

