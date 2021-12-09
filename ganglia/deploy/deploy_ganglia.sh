#!/usr/bin/env bash

host=$1
domain=$2
port=$3
user=$4

if [ "$#" -ne 4 ] ; then echo "USAGE: deploy_ganglia.sh hostname domain port user" && exit 1 ; fi

# Send configuration files/scripts to remote host

scp -P$port gmond.conf monitor.sh $user@$host.$domain:/tmp

# Process config file

awk '/\[PROCESS\]/{flag=1;next}/\[COMMAND\]/{flag=0}flag' configurations/$domain/$host.cfg | ssh -p$port $user@$host.$domain "cat > /tmp/$host.cfg"

# Run installation

ssh -tt -p$port $user@$host.$domain "sudo yum -y install epel-release; sudo yum -y install ganglia-gmond ganglia-gmond-python; sudo mv /tmp/gmond.conf /tmp/monitor.sh /tmp/host.cfg /etc/ganglia; sudo chmod +x /etc/ganglia/monitor.sh; echo \"echo '*/5 * * * * root /bin/sh /etc/ganglia/monitor.sh' > /etc/cron.d/ganglia\"|sudo bash; sudo service gmond restart gmond; sudo systemctl enable gmond; sudo /etc/ganglia/monitor.sh &>/dev/null;"

# Send config file to nagios server

r_ip=?   # Replace "?" with ip of nagios server
r_user=? # Replace "?" with username on nagios server
r_port=22

rsync -crpz -e "ssh -p$r_port" configurations $r_user@$r_ip:/etc/nagios

exit 0
