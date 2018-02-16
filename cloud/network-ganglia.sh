#!/bin/bash

initial_amount="/tmp/initial_amount"
touch $initial_amount
TZ='America/Vancouver'; export TZ

get_current_tx()
{
 #read statistics for eth0 only!
 cat /sys/class/net/eth0/statistics/tx_bytes
}

set_initial_tx()
{
 if [ "$(date +%H-%M)" == "00-00" ];
 then 
  get_current_tx > $initial_amount
 fi
 if [ "$(cat $initial_amount)" == "" ];
 then
  get_current_tx > $initial_amount
 fi
}

get_initial_tx()
{
 cat $initial_amount
}

send_stat()
{
 local group=$1
 local name=$2
 local value=$3
 local unit=$4
 gmetric -d 600 --cluster 'Belle-servers' --group $group --type 'int32' --name $name --value $value --unit $unit;
}



set_initial_tx
current_amount=$(get_current_tx)
initial=$(get_initial_tx)
todays_amount=$((current_amount-initial))
send_stat "Network" "send" $todays_amount bytes

