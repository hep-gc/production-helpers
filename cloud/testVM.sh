#!/bin/bash

checkforchild(){ 
 local parameter=$1;
 local tempvar=$(pgrep -P $1);
 if [ "$tempvar" != "" ]; 
 then 
  checkforchild $tempvar;
 else 
  echo $parameter; 
 fi 
}

gettime()
{
 local file=$1
 local timearray=($(ls -lt $file))
 #echo ${timearray[*]}
 timevalue="${timearray[5]} ${timearray[6]} ${timearray[7]}"
 date -d "$timevalue" "+%s" ;
}


let runtime=0; 
let runtime2=0; 
for i in $(ps axf|grep [c]ondor_starter|cut -d" " -f1);
do 
 lastpid=$(checkforchild $i);
 if [ "$(ps $lastpid|grep -c basf2)" == "0" ];
 then
  psarray=($(ps $(pgrep -P $i)|grep condor))
  name=$(dirname ${psarray[5]})
  file=$(ls -1art $name/D*/*.jdl|tail -n 1 )
  if [ -e $file ];
  then
   let runtime2=$(( $(date +%s) - $(gettime $file) ))
  else
   runtime2=0
  fi
  if [ $runtime2 -gt $runtime ];
  then
    runtime=$runtime2;
  fi;
 fi;
done;
basf2=$(ps axf|grep -c "[_] basf2");
cpus=$(grep processor /proc/cpuinfo -c); 
condor=$(ps axf|grep -c "[_] condor_starter"); 
filler=$(count=0;for j in $(find /var/lib/condor/execute/dir_*/ -maxdepth 1 -name DIRAC*);do number=$(grep -c 'exec.py' $(ls -t $j/*.jdl|head -n1));count=$((count+number));done;echo $count);
iparray=($(ip addr|grep "10.39"));
echo $basf2 $filler $condor $cpus $runtime ${iparray[1]};

