#!/usr/bin/env bash

SCRIPTS=/usr/local/nagios/etc/scripts

HOST_TEMPLATE=$SCRIPTS/generic_host.templ
GSVC_TEMPLATE=$SCRIPTS/generic_srvc.templ
PSVC_TEMPLATE=$SCRIPTS/process_srvc.templ

HOST_DIR=/usr/local/nagios/etc/objects/hosts
CFG_DIR=/etc/nagios/configurations

# Active hostnames from Ganglia
g_hostnames=( $(curl http://localhost/ganglia/dev/requestv2.php?action=list_hosts_col) )
g_hostaddrs=( $(curl http://localhost/ganglia/dev/requestv2.php?action=list_hosts_ip) )

# Hostnames registered with Nagios
IFS=$'\n' read -r -d '' -a n_hostnames < <(basename -a -s .cfg $HOST_DIR/*.cfg && printf '\0')

apply_config() {
	[ -f "$1" ] || return 1

	local mode=1 # 0 = command ; 1 = process

	while read line ; do
		if [[ ! -z $line ]]; then
			case "$line" in
				\[COMMAND\]) mode=0 && continue ;;
				\[PROCESS\]) mode=1 && continue ;;
			esac
			case "$mode" in
				0) arg_str=$( cut -d " " -f 1  <<< "$line"    )
				   svc_dsc=$( cut -d " " -f 2- <<< "$line"    )
				   metricn=$( cut -d "!" -f 1  <<< "$arg_str" )
				   sed "s/{{HOSTNAME}}/$2/g;s/{{METRIC}}/$metricn/g;s/{{ARGSTR}}/$arg_str/g;s/{{DESCRIPTION}}/$svc_dsc/g" $GSVC_TEMPLATE >> $HOST_DIR/$2.cfg
				   ;;
				1) sed "s/{{HOSTNAME}}/$2/g;s/{{SERVICE}}/$line/g" $PSVC_TEMPLATE >> $HOST_DIR/$2.cfg
				   ;;
			esac
		fi
	done < "$1"
}

add_host() {
	echo Adding host $1 with address $2
	
	sed "s/{{HOSTNAME}}/$1/g;s/{{HOSTADDR}}/$2/g" $HOST_TEMPLATE > $HOST_DIR/$1.cfg

	host=$(   cut -d "." -f 1  <<< "$1" )
	domain=$( cut -d "." -f 2- <<< "$1" )
	
	if [ -d "$CFG_DIR/$domain" ] ; then
		apply_config "$CFG_DIR/$domain/default.cfg" "$1" # Default settings for domain
		apply_config "$CFG_DIR/$domain/$host.cfg"   "$1" # Host-specific settings
	else    apply_config "$CFG_DIR/other/default.cfg"   "$1" ; fi # Unrecognized domain

}

new_hosts=0

for i in ${!g_hostnames[@]} ; do
	host=${g_hostnames[$i]}
	addr=${g_hostaddrs[$i]}
	if [[ ! " ${n_hostnames[*]} " =~ " ${host} "  ]] ; then
		add_host "$host" "$addr"
		new_hosts=$((new_hosts+1))
	fi
done

if [ "$new_hosts" = 0 ] ; then
	echo No new hosts to be added.
	exit 0
else
	echo $new_hosts new hosts were added.
	exit 1
fi

