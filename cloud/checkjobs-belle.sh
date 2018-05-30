#!/bin/bash

gethelp()
{
    echo " usage: ./checkjobs-belle.sh FILE DEFAULTNUMBER"
    echo "        FILE: file that contains the IP addresses of all VMs on the cloud"
    echo "     	  DEFAULTNUMBER: number of payload jobs that should run on the VM"
    echo ""
}

case $1	in
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




file=$1
let defaultnumber=$2
let defaultarray=$((defaultnumber-1))

for ip in $(cat $file)
do 
 number=($(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $ip "ps axf|grep -c '[_] bash basf2exec.sh' ; ps axf|grep -c '[_] condor_starter'" 2>/dev/null))
 #if [ ${number[0]} -lt $defaultnumber ]; #check if N(basf2) is less than it could be
 if [ ${number[0]} -lt ${number[1]} ] || [ ${number[0]} -eq 0 ];  #check if N(basf2) is less than N(condor)
 then
  unset jobslots
  for var in $(seq 0 $defaultarray)
  do
   jobslots[var]=slot0$((var+1))
  done
  for line in $(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $ip "ps axf|grep '[_] bash basf2exec.sh'|sed 's/^  *//g;'|cut -d' ' -f1" 2>/dev/null)
  do
    array=($(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $ip "ls -l /proc|grep $line" 2>/dev/null)); 
    okjobslot=(${array[2]}); 
    jobslots=("${jobslots[@]/$okjobslot}" )
   done  
  echo ${number[*]} $ip ${jobslots[*]}; 
fi; 
done
