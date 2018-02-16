#!/bin/bash

let minidle=150; #minimum idle jobs in queue before new ones can be submitted

loopvar=1; 
while [ $loopvar -eq 1 ]; 
do 
 if [ $(/usr/bin/condor_q|grep '00 I ' -c) -gt $minidle ]; 
 then 
  loopvar=0; 
 else 
  echo 'not enough jobs, waiting...';
  sleep 60;
 fi;
done
