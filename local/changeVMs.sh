#!/bin/bash
##################
#Global Variables#
##################
VO=belle
server=bellecs.heprc.uvic.ca
port=3121


######################
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

gethelp()
{
    echo " usage: ./changeVMs.sh CLOUD CPUs MAXAMOUNT IPSTRING INCREMENT SLEEPTIME"
    echo "         CLOUD    : name of the cloud information is wanted for"
    echo "         CPUs     : number of how many CPUs a VM on that cloud has"
    echo "         MAXAMOUNT: max number of VMs that should run through a specific cloudscheduler on CLOUD"
    echo "         IPSTRING : identifier for the IPs on that cloud to identify VMs that are not reachable, e.g.\"10.39\" "
    echo "         INCREMENT: amount by which the number of VMs is increased per interval"
    echo "         SLEEPTIME: time to wait until the number of VMs is increased again"
    echo ""
}

case $1	in
  help)
    gethelp
    exit
  ;;
esac

if [ "$#" -ne 6 ];
then
 gethelp
 exit
fi





provideIPFile()
{
 local cloud=$1
 ssh -t $server -p$port "./getinfo.sh $cloud ip >$cloud.ip" 
 scp -P $port $server:$cloud.ip . 
}

removeBadVMs()
{
 local cloud=$1
 local badIP=$2
 echo "$badIP is not reachable, terminating" >&2
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
 echo "    checking for errors..." >&2 
 checkerror $cloud $file
 echo scp to cloud: scp $file root@$cloud:. 
 scp $file $cloud:.
 echo "    checking for running payload..." >&2 
 ssh -A $cloud "./checkjobs-$VO.sh $file $CPUs" 2>/dev/null|while read line
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

############
# MAIN     #
############
while [ $start -eq 1 ] 
do 
 let missingbasf2=0
 let changedvar=0
 let temp=0
 echo getting IPs...
 provideIPFile $cloud &>/dev/null
 echo checking for basf2 status...
 lines=$(checkVMstatus $cloud $CPUs $searchString|grep slot|cut -d" " -f1)
 for i in  $lines
 do
  if [ "$i" == "" ]; then let temp=0;else let temp=$i;fi
  missingbasf2=$(( temp + missingbasf2))
 done 
 if [ $missingbasf2 -lt 10 ]; 
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
    timetosleep=$(($maxdiff*60)) 
    echo "sleeping an initial $maxdiff min at $(date)"
    sleep $timetosleep
  else
    echo "$missingbasf2 condor slots still not running basf2 at $(date)"
   timetosleep=$(($sleeptime*60)) 
   echo sleeping $sleeptime min...
   sleep $timetosleep
  fi 
 fi
done

