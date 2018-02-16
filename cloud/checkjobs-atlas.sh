#!/bin/bash

file=$1
let defaultnumber=$2
let defaultarray=$((defaultnumber-1))

for ip in $(cat $file)
do 
 number=($(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $ip "ps axf|grep -c '[a]thena.py' ; ps axf|grep -c '[_] condor_starter'" 2>/dev/null))
 #if [ ${number[0]} -lt $defaultnumber ] || [ ${number[0]} -eq 0 ]; 
 if [ ${number[0]} -lt ${number[1]} ] || [ ${number[0]} -eq 0 ]; 
 then
  unset jobslots
  for var in $(seq 0 $defaultarray)
  do
   jobslots[var]=slot0$((var+1))
  done
  for line in $(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $ip "ps axf|grep '[a]thena.py'|sed 's/^  *//g;'|cut -d' ' -f1" 2>/dev/null)
  do
    array=($(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $ip "ls -l /proc|grep $line" 2>/dev/null)); 
    okjobslot=(${array[2]}); 
    jobslots=("${jobslots[@]/$okjobslot}" )
   done  
  echo ${number[*]} $ip ${jobslots[*]}; 
fi; 
done
