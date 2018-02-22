#!/bin/bash
###################################
VO=belle
server=bellecs.heprc.uvic.ca
port=3121
##################################


gethelp()
{
    echo " usage: ./checkVMstatus.sh CLOUD CPUs"
    echo "        CLOUD: name of the cloud information is wanted for"
    echo "        CPUs : number of how many CPUs a VM on that cloud has"
    echo ""
}

case $1 in
  help)
    gethelp
    exit
  ;;
esac

if [ "$#" -ne 2 ];
then
 gethelp
 exit
fi


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
