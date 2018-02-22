#!/bin/bash
LANG=C

gethelp()
{
    echo " usage: ./getinfo.sh CLOUDNAME COMMAND"
    echo "        CLOUDNAME: name of the cloud, e.g.cc-west-b"
    echo "        COMMAND: nova commands or ip to get a list of IPs"
}

case $1 in
  help)
    gethelp
    exit
  ;;
esac

if [ "$#" -lt 2 ];
then
 gethelp
 exit
fi


cloudname=$1

OS_AUTH_URL=""
OS_TENANT_NAME=""
OS_USERNAME=""
OS_PASSWORD=""
port=""
region=""
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""

getconfig()
{
 local configfile="/etc/cloudscheduler/cloud_resources.conf"
 local cloud=$1
 sudo grep $cloud -A 20 $configfile|while read line
 do
  if [ "$line" == "" ];
  then 
   exit
  fi
  echo $line
 done
}

setconfig()
{
 local cloud=$1
 while read configoption
 do
  temparray=($configoption)
  case "${temparray[0]}" in
  auth_url)
   OS_AUTH_URL=${temparray[2]}
   ;;
  tenant_name)
   OS_TENANT_NAME=${temparray[2]}  
   ;;
  username)
   OS_USERNAME=${temparray[2]}  
   ;;
  password)
   OS_PASSWORD=${temparray[2]}  
   ;;
  port)
    port=${temparray[2]}
    ;;
  regions)
    region=${temparray[2]}
    ;;
  access_key_id)
    export AWS_ACCESS_KEY_ID=${temparray[2]}
    ;;
  secret_access_key)
    export AWS_SECRET_ACCESS_KEY=${temparray[2]}
    ;;
  esac 
 done< <(getconfig $cloud)
}

getCSVMs()
{
 local cloud=$1
 local field=$2
 #cloud_status -m 2>/dev/null|grep $cloud|grep -v "Retir"|cut -d" " -f$field #Does not give out retireing VMs
 cloud_status -m 2>/dev/null|grep $cloud|cut -d" " -f$field 
}

getOSVMs()
{
 nova --insecure --os-username $OS_USERNAME --os-password $OS_PASSWORD --os-tenant-name $OS_TENANT_NAME --os-auth-url $OS_AUTH_URL list 2>/dev/null|grep $cloudname|sed 's/|\|//g;'|while read line
 do
  echo "$line"|sed 's/ /_/g;'
 done
}

getIPs()
{
 local cloud=$1
 CSVMs=($(getCSVMs $cloud 1))
 OSVMs=($(getOSVMs $cloud))
 for i in ${CSVMs[*]}
 do
  for j in ${OSVMs[*]}
  do
   if [[ $j =~ $i ]]
   then
    echo $j|cut -d"=" -f2 |cut -d"," -f1
   fi
  done
 done
}

getamazonIPs()
{
 local cloud=$1
 getCSVMs $cloud 2|sed 's/\./-/g;'|cut -d"-" -f 2,3,4,5|sed 's/-/./g;'
}

IPs()
{
 local cloud=$1
 if [[ $cloud =~ amazon ]]
 then
  getamazonIPs $cloud
 else
  setconfig $cloud
  getIPs $cloud
 fi
}

listVMs()
{
 local cloud=$1
 local command=$2
 setconfig $cloud
 if [[ $cloud =~ amazon ]]
 then
   aws ec2 describe-instances --region $region --output text|grep INSTANCES|sed 's/\t */ /g;'|cut -d" " -f14
 else
  nova --insecure --os-username $OS_USERNAME --os-password $OS_PASSWORD --os-tenant-name $OS_TENANT_NAME --os-auth-url $OS_AUTH_URL $command 2>/dev/null
 fi
}


novacommand()
{
 local cloud=$1
 local command=$2
 local option=$3
 setconfig $cloud
 if [[ $cloud =~ amazon ]]
 then
  echo $cloud not supported for executing nova commands
 else
  nova --insecure --os-username $OS_USERNAME --os-password $OS_PASSWORD --os-tenant-name $OS_TENANT_NAME --os-auth-url $OS_AUTH_URL $command $option 2>/dev/null
 fi
}

case $2 in
 ip)
  IPs $cloudname
  exit
  ;;
 list)
  listVMs $cloudname $2 
  exit
  ;;
 *)
  novacommand $cloudname $2 $3
esac
exit
