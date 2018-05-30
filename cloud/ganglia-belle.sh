#!/bin/bash

file=$1
let basf2number=0
let fillernumber=0
let totalnumber=0
let cpunumber=0
number=("1" "2" "3")
rm -f /tmp/file*

getnumber()
{
 local host=$1
 local counter=$2
 scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null testVM.sh root@$host:.
 ssh -c arcfour -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n -l root $host "./testVM.sh $host" 2>/dev/null >/tmp/file$counter
}

let counter=0
for i in $(cat $file)
do
 getnumber $i $counter &
 counter=$((counter+1))
done

wait
let counter2=0
counter=$((counter-1))
for i in $(seq 0 $counter)
do
 numberarray=($(cat /tmp/file$i))
 let basf2number=$((basf2number+numberarray[0]))
 let fillernumber=$((fillernumber+numberarray[1]))
 let totalnumber=$((totalnumber+numberarray[2]))
 let cpunumber=$((cpunumber+numberarray[3]))
 if [ "${numberarray[4]}" != "0" ]; then echo runtime4=${numberarray[4]} at ${numberarray[5]};let runtime=$((runtime+numberarray[4])); counter2=$((counter2+1));fi
done
 let counter=$((counter+1))
 if [ "$counter2" != "0" ];
 then
  let runtime=$((runtime/counter2/60))
 else
  let runtime=0
 fi

 echo counter2=$counter2

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
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'number_VMs' --value $counter --unit 'Percentage' 
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'average_runtime_without_basf2' --value $runtime --unit 'minutes' 
gmetric --cluster 'Belle-servers' --group 'BelleJobs' --type=uint16 --name 'VMs_with_pilots_without_basf2' --value $counter2 --unit 'Amount' 


