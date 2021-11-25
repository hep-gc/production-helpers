# @AUTHOR: Victor Kamel

import os
import pickle
import numpy as np
import pandas as pd
import itertools as it

from hashlib import md5
from datetime import datetime, timedelta

class Data:
    """
    Transform data requested from Ganglia into correct format for anomaly
    detection with PyOD-based detector.
    """
    
    def __init__(self, host, start_time, end_time, resolution, api, step, slide, coeffs = None):
        """
        Initialization.
        host:       Hostname
        start_time: Start date/time (unix timestamp or AT-Style time)
        end_time:   End date/time (unix timestamp or AT-Style time)
        resolution: Data aggregation resolution (mean)
        api:        Instance of GangliaAPI or compatible module
        step:       Number of data points per window
        slide:      Number of data points before new window is started (if slide=step then windows are non-overlapping)
        coeffs:     Normalization coefficients. Should be provided for inference data but not training data.
        """
        
        self.cluster, self.host, self.metrics = host
        self.start, self.end = start_time, end_time
        self.coeffs = coeffs
        
        self.fetch_data(api, resolution, step, slide)
    
    def fetch_data(self, api, resolution, step, slide):
        """
        Get data from API.
        """
        
        r = api.get_data(self.cluster, self.host, ",".join(self.metrics), self.start, self.end, resolution)
        assert isinstance(r, dict), r
        
        if self.coeffs is None: coeffs = {}
        
        # Save a series representation of data
        self.series = pd.DataFrame({metric : [x[1] for x in r[metric]] for metric in r}, index=[x[0] for x in r[list(r)[0]]], dtype=np.float64)
        self.series.index = self.series.index.astype(float).map(datetime.fromtimestamp)
        
        windows = {}
        
        # Make sure that data is returned in the correct order
        assert list(r) == self.metrics, r
        
        # Iterate metrics
        for metric in r:
            
            # Split data
            timestamps, data = zip(*r[metric])
            data = np.array(data, dtype=np.float32)
            
            assert not np.isnan(data).any(), f"WARNING: Data for {self.host} from {timestamps[0]} to {timestamps[-1]} contains non-numeric values."

            # Normalize data
            if self.coeffs is None:
                mean, std = data.mean(), data.std()
                data = self._transform(data, mean, std)
                coeffs[metric] = (mean, std)
            else: data = self._transform(data, *self.coeffs[metric])
            
            # Slice data into windows
            for i in range(0, len(data) - step + 1, slide):
                ts, ds = timestamps[i], list(data[i: i + step])
                
                if ts in windows: windows[ts].extend(ds)
                else:             windows[ts] = [ts, self.host, self.host] + ds
        
        # Save coeffs
        if self.coeffs is None: self.coeffs = coeffs
        
        # Create final window dataframe
        self.windows = pd.DataFrame(windows.values(), columns = ["timestamp", "hostname", "hostgroup"] + list(it.chain.from_iterable([[f'{metric}_{x}' for x in range(step)] for metric in self.metrics])))
    
    def get_norm_coeffs(self): return self.coeffs  # Return calculated normalization coefficients
    def get_windows(self):     return self.windows # Return data as set of windows DataFrame (for anomaly detection)
    def get_series(self):      return self.series  # Return data as series DataFrame (for graphing)
    def get_raw(self):         return self.windows.drop(["timestamp", "hostname", "hostgroup"], axis=1) # Return windows only (no labels)
    def get_provenance(self):  return self.windows[["timestamp", "hostname"]]                           # Return labels only (no windows)
    def _transform(self, val, mean, std): return (val - mean) / std # Normalize data
        