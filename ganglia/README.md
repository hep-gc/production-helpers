# Useful tools for Ganglia

## Managing the RRDTool database files:

### `merge-rrd.py`

```
Usage: merge-rrd.py <old rrd> <new rrd> <merged rrd>
    
merge-rrd.py is a python script that merges that data found in rrd
files. This assumes that the two rrds are have the same data structure.

The script creates the merged rrd by copying the entries from the new rrd.
If the new rrd has database entries with missing data, then the records
of the old rrd are used instead. This mean that data from the new rrd
will always take precedence over the data in the old rrd.
```

### `merge-hosts.sh`

```
USAGE: merge-hosts.sh <old host dir> <new host dir> <dest host dir>

A shell script that runs merge-rrd.py on all pairs of files in the old/new
host directories and places the resulting merged file into the destination
directory.

If a file in the old host directory does not have a new counterpart, the file
will be copied to the destination directly.
```