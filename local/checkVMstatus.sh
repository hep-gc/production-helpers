#!/bin/bash
###################################
VO=belle
server=bellecs.heprc.uvic.ca
port=3121
##################################

cloud=$1
CPUs=$2

echo cloud=$cloud and CPUs=$CPUs
echo getting IPs...
ssh -tt $server -p$port "./getinfo.sh $cloud ip >$cloud.ip" 2>/dev/null
scp -P $port $server:$cloud.ip .
echo scp to cloud: scp $cloud.ip root@$cloud:. 
scp  $cloud.ip root@$cloud:. 
date 
echo checking....
ssh -A $cloud "./checkjobs-$VO.sh $cloud.diff $CPUs" 2>/dev/null
