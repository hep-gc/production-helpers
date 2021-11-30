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
    import pandas as pd
    
    import matplotlib.pyplot  as plt
    import matplotlib.patches as mpatches
    import matplotlib.dates   as mdates
    import concurrent.futures
    import subprocess
    import importlib
    import socket
    import sys
    import os

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
    else: print("Unable to save model. Continuing.")
        
def load_model(filename):
    """
    Load anomaly detection model and normalization coefficients to a file.
    """
    if   det_type[1]  == 'IForest'  : return load(filename)
    elif det_type[1]  == 'AELstmTF2':
        model, train_data = load(filename + "_object")
        model.model_ = tf.keras.models.load_model(filename)
        return model, train_data

def annotate_period(ax, start, delta, text=''):
    """
    Label period of time on plot.
    Label starts at start and ends at start + delta.
    """
    ax.annotate("", xy=(start - 0.002, 1.15), xytext=(start + delta + 0.002, 1.15), xycoords=ax.transAxes, arrowprops=dict(arrowstyle='|-|', linewidth=1))
    ax.annotate("", xy=(start - 0.002, 1.15), xytext=(start + delta + 0.002, 1.15), xycoords=ax.transAxes, arrowprops=dict(arrowstyle='<->', linewidth=1))
    ax.annotate(text, xy=(start + (delta / 2), 1.15), xycoords=ax.transAxes, ha='center', va='center', bbox=dict(fc="white", ec="none"), fontsize=12)

def generate_plot(hostname, metrics, predictions, series):
    """
    Generate a plot for a given host with anomalous windows highlighted.
    """
    # Config
    fig, axes = plt.subplots(len(metrics), 1, figsize=(15, 10), sharey='row', sharex='col')
    fig.suptitle(f'Host: {hostname}', y=0.95)
    fig.subplots_adjust(wspace=0, hspace=0.2)
    
    td = datetime.fromtimestamp(today)
    fmt = mdates.DateFormatter("%B %d, %Y")

    train_steps = train_days * (86400 // (resolution * steps)) # Steps in training period
    step_prop   = 1 / (train_steps + len(predictions))     # Proportion per step
    annotate_period(axes[0], 0, train_steps * step_prop, "$Training\ period$")
    
    # Add plots to axes
    for ax, metric, c in zip(axes, metrics, plt.rcParams["axes.prop_cycle"]()):

        ax.plot(series.index, list(series[metric]), label=metric, color=c['color'])
        ax.xaxis.set_tick_params(rotation=30)
        ax.xaxis.set_major_formatter(fmt)
        ax.legend(loc='upper left')
        ax.margins(x=0)
        
        # Training period
        ax.axvspan(td - timedelta(days=train_days), td, alpha=0.25, color='skyblue')

        # Inference period
        for x in range(len(predictions)):
            ax.axvline(x = td + timedelta(hours=8*x, minutes=-5), color = 'black', linewidth=1, alpha=0.5)
            annotate_period(axes[0], train_steps * step_prop + x * step_prop, step_prop, f"${x+1}$")
            if predictions[x]:
                ax.axvspan(td + timedelta(hours=8*x, minutes=-5), td + timedelta(hours=8*(x+1), minutes=-5), alpha=0.25, color='red')

    fig.legend(handles=[mpatches.Patch(color='skyblue', alpha=0.25, label='$Training\ Period$'),
                        mpatches.Patch(color='red', alpha=0.25, label='$Anomaly\ detected$'),
                        mpatches.Patch(edgecolor='black', alpha=0.25, label='$OK$', fill=False)])
    
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
    hashstr = f"{host[1]}_{today}_{hash_objects(host, model, look_behind, offset, resolution, API, steps, slide, det_type)}"
    
    if len(host) == 5: # Allow setting a clustom training window
        start_time = int(host[3])
        end_time   = int(host[4])
    
    # Try to load model from cache
    if hashstr in os.listdir('cache'): detector, train_data = load_model(f"cache/{hashstr}")
    else:
        # Get training data, get normalization coeffs
        
        if len(host) == 5:
            start_time, end_time = host[3:5]
            if start_time.isdigit(): start_time = int(start_time) - offset
            if end_time.isdigit(): end_time = int(end_time) - offset
            
            train_data = Data(host[:3], start_time, end_time, resolution, API, steps, slide)
        else:
            train_data = Data(host[:3], look_behind, today - offset, resolution, API, steps, slide)

        # Initialize model
        detector = det(**model)
        if det_type[1] == 'AELstmTF2': detector._set_n_classes(None)
        # Fit model
        detector.fit(train_data.get_raw())
        # Save model
        save_model(detector, train_data, f"cache/{hashstr}")
    
    # Fetch inference data
    infer_data = Data(host[:3], today - offset, f's+{8 * nwindows}h', resolution, API, steps, 48, coeffs=train_data.get_norm_coeffs())
    
    # Generate predictions
    infer = infer_data.get_raw()
    predictions = detector.predict(infer)
    
    # Generate plots if there are any anomalous hosts
    if (not DEBUG) and any(predictions): generate_plot(*host[1:3], predictions, pd.concat([train_data.get_series(), infer_data.get_series()]))
    
    return (*host[0:2], detector.predict_proba(infer), detector.decision_function(infer), predictions, detector.threshold_)

# Entry
if __name__ == "__main__":
    
    # Parse command line arguments
    args = sys.argv
    if   len(args) == 1: config_file = 'config.txt'
    elif len(args) == 2: config_file = args[1]
    else:
        print("USAGE: run_analysis.py [config_file]")
        exit(1)
    
    # Create output/cache folders
    if not os.path.exists('cache') : os.makedirs('cache')
    if not os.path.exists('output'): os.makedirs('output')
       
    # Load configuration file
    config, hosts, model = load_config(config_file)
    
    # Required configuration options
    API  = GangliaAPI(config['monitor_server'])

    det_type = (*config['detector'].rsplit('.', 1),)
    det = getattr(importlib.import_module(det_type[0]), det_type[1])
    
    # Optional configuration options
    silent = int(config.get('silent', 0))
    admin_email = config.get('admin_email', None)
    if admin_email is None: silent = 1
    
    train_days  = int(config.get('train_days',  7))
    max_workers = int(config.get('max_workers', 1))
    
    # By Default:
    # Data pulled  : 1 Week (Training), 1 Day (Inference)
    # Aggregated   : Every 10 Minutes (AVERAGE)
    # Windows size : 48 (3 8-hours windows per day since there are 144 10min chunks per day)

    # Define data parameters
    today       = int(date.today().strftime("%s"))
    now         = int(datetime.today().strftime("%s"))
    look_behind = f'e-{train_days}days' # Length of training dataset - 1 wk from end
    offset      = 1200                  # RRDTool align to boundary correction

    # Window length, Steps to begin new window, Aggregation interval
    steps, slide, resolution= 48, 1, 600
    
    # Number of available windows
    nwindows   = 3 if today < int(date.today().strftime("%s")) else (now - today) // (steps * resolution)
    
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
            if file.endswith(".png"):
                print(f"Removing {file}")
                os.unlink(f'output/{file}') 
    
    with progress("Running analysis"):
        with concurrent.futures.ProcessPoolExecutor(max_workers=1 if DEBUG else max_workers) as executor:
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
            for c in range(len(verd)): report += (f"\tWindow {c+1} ({w[c]}):"
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
    
            if (not DEBUG) and (not silent):
                send_report(
                    f'Anomaly report {datetime.today().strftime("%x %I:%M %p")}',
                    f"Anomaly Detection System <noreply@{socket.getfqdn()}>",
                    admin_email, out, anomalous_hosts)
                
                # Remove plot image files
                for host in anomalous_hosts: os.unlink(f'output/{host[1]}.png')
            elif silent: print("Note: Silent mode is on.")
    
        else: out = "No anomalies were detected.\n\n-----\n\n" + report
        
        print(out.replace('Anomaly Detected', '\033[31mAnomaly Detected\033[0m')
                 .replace('OK', '\033[32mOK\033[0m'))
    
    

