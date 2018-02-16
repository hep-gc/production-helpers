#!/bin/bash

##################
#Global Variables#
##################
server=bellecs.heprc.uvic.ca
port=3121

cloud=$1 
CPUs=$2 
maxamount=$3
searchString=$4
interval=$5
sleeptime=$6
newamount=0
temparray=("")
currentN=0
maxN=0
start=1
#####################

provideIPFile()
{
 local cloud=$1
 ssh -t $server -p$port "sudo ./getinfo.sh $cloud ip >$cloud.ip" 
 scp -P $port $server:$cloud.ip . 
}

removeBadVMs()
{
 local cloud=$1
 local badIP=$2
 echo "$badIP is bad" >&2
 ssh -tt  -p$port $server  "sudo ./getinfo.sh $cloud list|grep \"$badIP  \"|cut -d' ' -f2|xargs cloud_admin -c $cloud -k -n " &>/dev/null &&  echo removed $badIP 
}

checkerror()
{
 local file=$2
 local cloud=$1
 for i in $(grep $cloud $file |cut -d_ -f1)
 do
  ssh -tt  -p$port $server  "cloud_admin -c $cloud -k -n $i" &>/dev/null &&  echo removed badVM >&2
  sed -i "/$i/d" $file
 done 
}

checkVMstatus()
{
 local cloud=$1
 local CPUs=$2
 local searchstring=$3
 local file="$cloud.ip"

 echo cloud=$cloud and CPUs=$CPUs 
 echo getting IPs... 
 if [ -f $cloud-ok.ip ]; 
 then
  grep -F -x -v -f $cloud-ok.ip $cloud.ip >$cloud.diff
  file="$cloud.diff"
 fi
 echo checking for errors.... >&2 
 checkerror $cloud $file
 echo scp to cloud: scp $file root@$cloud:. 
 scp $file $cloud:.
 date  ssh -A $cloud "./checkjobs.sh $file $CPUs" 2>/dev/null|while read line
 do
  badIP=$(echo $line|grep  "^$searchstring"|cut -d" " -f1)
  if [ "$badIP" != "" ];
  then
    removeBadVMs $cloud $badIP 
  else
   echo $line
  fi
 done
}


testqueue()
{
  ssh -t $server -p$port ./testqueue.sh
}

while [ $start -eq 1 ] 
do 
 let changedvar=0
 echo getting IPs...
 provideIPFile $cloud &>/dev/null
 echo checking for basf2 status...
 let missingbasf2=$(checkVMstatus $cloud $CPUs $searchString|grep -c slot)
 if [ $missingbasf2 -eq 0 ]; 
 then 
  temparray=($(ssh $server -p$port "cloud_status -c $cloud" 2>/dev/null|grep True)) 
  let currentN=${temparray[2]}
  let maxN=${temparray[4]}
  if [ $currentN -eq $maxN ];
  then 
    maxdiff=$((maxamount-maxN))  
    if [ $maxdiff -gt $interval ];
    then
     maxdiff=$interval
    fi
    newamount=$((maxN+maxdiff))
    echo testing if enough idle jobs are available...
    testqueue &>/dev/null
    echo change to $newamount VMs on $cloud...
    ssh $server -p$port "cloud_admin -c $cloud -v $newamount" 2>/dev/null
    mv $cloud.ip $cloud-ok.ip
    let changedvar=1
  fi; 
 fi
 if [ $newamount -eq $maxamount ];
 then
  echo "reached max number of VMs ($newamount) on $cloud at $(date)"
  start=0  
 else 
  if [ $changedvar -eq 1 ];
  then
    echo "waiting for $maxdiff new VMs to start..."
  else
    echo "$missingbasf2 new VM(s) still not running basf2 at $(date)"
  fi 
  timetosleep=$(($sleeptime*60)) 
  echo sleeping $sleeptime min...
  sleep $timetosleep
 fi
done

