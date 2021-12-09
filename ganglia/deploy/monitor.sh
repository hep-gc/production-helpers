#!/usr/bin/env bash

METRIC_TTL=905
PROC_CFG=/etc/ganglia/host.cfg

ssh_whitelist=( 'uvic.ca' )

# Commands to gather metrics

proc_verify() {
        if [ $(ps axf|grep -c "$1") -gt 1 ];then echo "True"
        else                                  echo "False" ; fi
}


check_ssh_connections() {
  unknown=0
  for host in $(last -w | grep "still logged in" | awk '{print $3}' | uniq); 
  do
      hostname=$(getent hosts $host | awk '{print tolower($2)}')
      [[ $hostname =~ ^.*($ssh_whitelist)$ ]] || unknown=$((unknown+1))
  done
  echo $unknown
}

SWAP_PERCENT=$(free -t | grep -i swap|awk '{print $3/$2*100}')

# TYPES: string|int8|uint8|int16|uint16|int32|uint32|float|double

gmetric -n 'Swap_Usage' -v $SWAP_PERCENT -t 'uint16' -u '%' -d $METRIC_TTL
gmetric -n 'Unknown_SSH_Connections' -v $(check_ssh_connections) -t 'uint16' -u 'Connections' -d $METRIC_TTL

while read proc ; do 
  if [ $proc != "" ]; 
  then
    gmetric -n $proc'_service_running' -v $(proc_verify $proc) -t 'string' -u '' -d $METRIC_TTL
  fi
done < $PROC_CFG
                          