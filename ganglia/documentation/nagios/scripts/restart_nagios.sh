#!/usr/bin/env bash

now=`date +%s`
commandfile='/usr/local/nagios/var/rw/nagios.cmd'

/bin/printf "[%lu] RESTART_PROGRAM\n" $now > $commandfile
