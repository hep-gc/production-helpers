#!/usr/bin/env bash

# Merge (OLD -> NEW) -> DEST

if [ "$#" -ne 3 ] ; then
	echo "USAGE: merge-hosts.sh path/to/old/host/files path/to/new/host/files path/to/destination/files"
fi

OLD=$1 ; NEW=$2 ; DEST=$3


for file in $(basename -a "$OLD"/*.rrd) ; do

	if [ ! -f "$NEW"/"$file" ] ; then
		echo "File $file has no new copy to merge with. Copying directly."
		cp "$OLD"/"$file" "$DEST"/"$file"
	else
		./merge-rrd.py "$OLD"/"$file" "$NEW"/"$file" "$DEST"/"$file"
	fi

done
