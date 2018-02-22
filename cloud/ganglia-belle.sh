#!/bin/bash

gethelp()
{
    echo " usage: ./ganglia-belle.sh FILE "
    echo "        FILE: file that contains the IP addresses of all VMs on the cloud"
    echo ""
}

case $1	in
  help)
    gethelp
    exit
  ;;
esac

if [ "$#" -ne 1 ];
then
 gethelp
 exit
fi



file=$1
let basf2number=0
let fillernumber=0
let totalnumber=0
let cpunumber=0
number=("1" "2" "3")


getnumber()
{
 local host=$1
 local counter=$2
 ssh -c arcfour -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n -l root $host 'basf2=$(ps axf|grep -c "[_] bash basf2exec.sh");cpus=$(grep processor /proc/cpuinfo -c); condor=$(ps axf|grep -c "[_] condor_starter"); filler=$(count=0;for j in $(find /var/lib/condor/execute/dir_*/ -maxdepth 1 -name DIRAC*); do number=$(grep -c 'exec.py' $(ls -t $j/*.jdl|head -n1));count=$((count+number)); done;echo $count); echo $basf2 $filler $condor $cpus' 2>/dev/null >/tmp/file$counter
}

let counter=0
for i in $(cat $file)
do
 getnumber $i $counter &
 counter=$((counter+1))
done

wait
counter=$((counter-1))
for i in $(seq 0 $counter)
do
 numberarray=($(cat /tmp/file$i))
 let basf2number=$((basf2number+numberarray[0]))
 let fillernumber=$((fillernumber+numberarray[1]))
 let totalnumber=$((totalnumber+numberarray[2]))
 let cpunumber=$((cpunumber+numberarray[3]))
done


if [ $totalnumber -eq 0 ]; 
then
 basf2ratio=0
 fillerratio=0
else
  basf2ratio=$(echo "scale=0;100*$basf2number/$totalnumber"|bc -l)
  fillerratio=$(echo "scale=0;100*$fillernumber/$totalnumber"|bc -l)
fi
if [ $cpunumber -eq 0 ];
then
 jobratio=0
else
 jobratio=$(echo "scale=0;100*$totalnumber/$cpunumber"|bc -l)
fi

gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'basf2_jobs' --value $basf2number --unit 'Amount' 
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'filler_jobs' --value $fillernumber --unit 'Amount' 
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'all_jobs' --value $totalnumber --unit 'Amount'
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'CPUs' --value $cpunumber --unit 'Amount' 
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'basf2_ratio' --value $basf2ratio --unit 'Percentage' 
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'filler_ratio' --value $fillerratio --unit 'Percentage'
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'condor_ratio' --value $jobratio --unit 'Percentage' 


