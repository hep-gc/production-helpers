#!/bin/bash

action=$1
quantity=$2
file=$3 

gfal_mount()
{
 local IP=$1
 local counting=$2
 if [ "$(ssh  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -l root -n $IP 'grep -c ^\#/usr/local/bin/create-mount.sh /etc/profile.d/grid-setup.sh')" == "1" ];
 then
  ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP " sed 's/#\/usr\/local\/bin\/create-mount\.sh/\/usr\/local\/bin\/create-mount\.sh/g;' -i /etc/profile.d/grid-setup.sh"
  if [ $counting -eq 0 ];
  then
   echo 1
  else
   ((amount++))
  fi
 else 
  echo 0
 fi
}

gfal_use()
{
 local IP=$1
 local counting=$2
 if [ "$(ssh -l root  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP grep -c \"^\#export VO_BELLE_DATA\" /etc/profile.d/grid-setup.sh )" == "1" ];
 then
   ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP " sed 's/#export VO_BELLE_DATA/export VO_BELLE_DATA/g;' -i /etc/profile.d/grid-setup.sh"
  if [ $counting -eq 0 ];
  then
   echo 1
  else
   ((amount++))
  fi
 else
  echo 0
 fi
}

gfal_onthefly()
{
 local IP=$1
 local counting=$2
 if [ "$(ssh  -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP grep -c \"^\#export VO_BELLE_TAR\" /etc/profile.d/grid-setup.sh )" == "1" ];
 then
   ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP " sed 's/#export VO_BELLE_TAR/export VO_BELLE_TAR/g;' -i /etc/profile.d/grid-setup.sh"
  if [ $counting -eq 0 ];
  then
   echo 1
  else
   ((amount++))
  fi
 else
  echo 0
 fi
}

gfal_notonthefly()
{
 local IP=$1
 local counting=$2
 if [ "$(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP grep -c \"^export VO_BELLE_TAR\" /etc/profile.d/grid-setup.sh )" == "1" ];
 then
  ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP " sed 's/export VO_BELLE_TAR/#export VO_BELLE_TAR/g;' -i /etc/profile.d/grid-setup.sh"
  if [ $counting -eq 0 ];
  then
   echo 1
  else
   ((amount++))
  fi
 else
  if [ $counting -eq 0 ];
  then
   echo 0
  fi
 fi
}

gfal_unuse()
{
 local IP=$1
 local counting=$2
 if [ "$(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP grep -c \"^export VO_BELLE_DATA\" /etc/profile.d/grid-setup.sh )" == "1" ];
 then
  ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP " sed 's/export VO_BELLE_DATA/#export VO_BELLE_DATA/g;' -i /etc/profile.d/grid-setup.sh"
  if [ $counting -eq 0 ];
  then
   echo 1
  else
   ((amount++))
  fi
 else
  echo 0
 fi
}


gfal_unmount()
{
 local IP=$1
 local counting=$2
 if [ "$(ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP 'grep ^/usr/local/bin/create-mount.sh -c /etc/profile.d/grid-setup.sh ')" == "1" ];
 then
   ssh -l root -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -n $IP " sed 's/\/usr\/local\/bin\/create-mount\.sh/#\/usr\/local\/bin\/create-mount\.sh/g;' -i /etc/profile.d/grid-setup.sh"
  if [ $counting -eq 0 ];
  then
   echo 1
  else
   ((amount++))
  fi
 else
  echo 0
 fi
}

gfal_enable()
{
 local IP=$1
 local count=0
 count=$((count+$(gfal_mount $IP 0)))
 count=$((count+$(gfal_use $IP 0)))
 count=$((count+$(gfal_onthefly $IP 0)))
 if [ $count -eq 3 ];
 then
  ((amount++))
 fi
}

gfal_disable()
{
 local IP=$1
 local count=0
 count=$((count+$(gfal_unmount $IP 0)))
 count=$((count+$(gfal_unuse $IP 0)))
 count=$((count+$(gfal_notonthefly $IP 0)))
 if [ $count -eq 3 ];
 then
  ((amount++))
 fi
}

gfal_check()
{
 local IP=$1
 ((counter++))
  local array=($(ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -l root -n $IP "
  grep -c ^/usr/local/bin/create-mount.sh /etc/profile.d/grid-setup.sh; 
  grep -c \"^export VO_BELLE_DATA\" /etc/profile.d/grid-setup.sh; 
  grep -c \"^export VO_BELLE_TAR\" /etc/profile.d/grid-setup.sh " 2>/dev/null))
  echo 'number' $counter' :  '$IP' :  mount : '${array[0]}  usage : ${array[1]} on-the-fly : ${array[2]}
}

let amount=0
let counter=0
while read IPs
do
 case $action in
  mount)
    gfal_mount $IPs 1
    echo $IPs checked, amount=$amount
    ;;
  unmount)
    gfal_unmount $IPs 1
    echo $IPs checked, amount=$amount
    ;;
  use)
    gfal_use $IPs 1
    echo $IPs checked, amount=$amount
    ;;
  unuse)
    gfal_unuse $IPs 1
    echo $IPs checked, amount=$amount
    ;;
  onthefly)
    gfal_onthefly $IPs 1
    echo $IPs checked, amount=$amount
    ;;
  notonthefly)
    gfal_notonthefly $IPs 1
    echo $IPs checked, amount=$amount
    ;;
  enable)
    gfal_enable $IPs
    echo $IPs checked, amount=$amount
    ;;
  disable)
    gfal_disable $IPs
    echo $IPs checked, amount=$amount
    ;;
  check)
    gfal_check $IPs
    ;;
 esac
 if [ $amount -eq $quantity ];
 then
  exit
 fi
done < <(cat $file)
echo $amount


