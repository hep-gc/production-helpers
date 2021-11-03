#!/usr/bin/env python3
"""
    merge-rrd.py
    
    This script takes rrds with the same structure and merges them 
    into a new rrd with the combined data.

    Modified by Victor Kamel (2021) Python 2 -> 3
"""

import sys, os, re
from subprocess import Popen, PIPE, STDOUT

reSearchCF   = re.compile("<cf>(.*)</cf>"                      ).search
reSearchPDP  = re.compile("<pdp_per_row>(.*)</pdp_per_row>"    ).search
reSearchRow  = re.compile(" / (\d+) --> <row><v>(.*)</v></row>").search
reMatchDBEnd = re.compile(".*</database>"                      ).match

def printUsage():
    """Prints help information"""
    print("""
    Usage: merge-rrd.py <old rrd> <new rrd> <merged rrd>
    
    merge-rrd.py is a python script that merges that data found in rrd
    files.  This assumes that the two rrds are have the same data structure.
    
    The script creates the merged rrd by copying the entries from the new rrd.
    If the new rrd has database entries with missing data, then the records
    of the old rrd are used instead.  This mean that data from the new rrd
    will always take precedence over the data in the old rrd.
    
    """)
    
def getXmlDict(xml):
    """Reads in rrd xml and returns a dictionary of lists
    
    The dictionary key is "<cf><pdp-per-row>". e.g.: AVERAGE1 or MAX6
    The list is the database entries for this <rra>
    """
    #    <cf> AVERAGE </cf>
    #    <pdp_per_row> 288 </pdp_per_row> <!-- 86400 seconds -->

    rrd_d = {}

    # parse xml file
    
    key = ""
    rows = {} 
    for line in xml.splitlines():
        
        m = reSearchRow(line)
        if m: 
            if m[2] != "NaN": rows[m[1]] = [m[2], line]
            continue
        
        m = reSearchCF(line)
        if m:
            key += m[1]
            continue

        m = reSearchPDP(line)
        if m:
            key += m[1]
            continue
        
        if reMatchDBEnd(line) and key and rows:
            rrd_d[key] = rows
            key = ""
            rows = {}
    
    return rrd_d

def mergeRRD(opath, npath, mpath):
    """Combines old and cur rrd to create new one"""  
    
    oxml  = Popen(['rrdtool', 'dump', opath], stdout=PIPE, stdin=PIPE, stderr=PIPE).communicate()[0].decode()
    odict = getXmlDict(oxml)
    nxml  = Popen(['rrdtool', 'dump', npath], stdout=PIPE, stdin=PIPE, stderr=PIPE).communicate()[0].decode()

    tmp = mpath + "_tmp.xml"
    mxmlf = open(tmp,'w')
    
    # look for matches to replace and upate current file
    key = ""
    
    for line in nxml.splitlines():
        
        m = reSearchRow(line)
        if m and m[2] == "NaN":
            if key in odict and m[1] in odict[key]: line = odict[key][m[1]][1]
        
        else:

            m = reSearchCF(line)
            if m: key += m[1]

            m = reSearchPDP(line)
            if m: key += m[1]
        
            # end of rra is reached, reset key
            if reMatchDBEnd(line): key = ""
        
        mxmlf.write(f"{line}\n")
    
    mxmlf.close()

    # create new rrds
    Popen(['rrdtool', 'restore', os.path.join(tmp), mpath], stdout=PIPE, stdin=PIPE, stderr=PIPE).communicate()

    # remove tmp.xml
    os.unlink(tmp)

### start of script ###
if __name__ == "__main__":

    if (len(sys.argv) != 4):
        print("merge-rrd.py take 3 arguments")
        printUsage()
        sys.exit(1)
        
    old_path, new_path, mer_path = sys.argv[1:4]

    if (mer_path == old_path):
        print("WARN: you are trying to overwrite your old rrd:%s"%(old_path,))
        printUsage()
        sys.exit(1)
    if (mer_path == new_path):
        print("WARN: you are trying to overwrite your new rrd:%s"%(new_path,))
        printUsage()
        sys.exit(1)
    if (os.path.exists(mer_path)):
        print("WARN: your merged rrd already exits.  Please remove it first:%s"%(mer_path,))
        printUsage()
        sys.exit(1)
        
    print("merging old: %s to new: %s. creating merged rrd: %s"%(old_path,new_path,mer_path))
    mergeRRD(old_path, new_path, mer_path)

