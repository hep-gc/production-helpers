# Installation

These scripts need to be in $HOME on a machine that has access to the worker nodes on a cloud and which can be reached by "ssh -A" using a ssh-key that also allows access to the worker nodes.


# Description

## changegfalfs.sh

A tool that changes the usage of gfalFS for Belle-II jobs.


usage: ./changegfalfs.sh ACTION QUANTITY FILE

ACTION : one of {mount, unmount, use, unuse, onthefly, notonthefly, enable, disable, check}

         mount/unmount        = enables/disables the gfalFS mount for new jobs on a VM
         use/unuse            = enables/disables the usage of the gfalFS mount for new jobs on a VM
         onthefly/notonthefly = enables/disables untar-on-the-fly for new jobs on a VM
         enable/disable       = enables/disables all the above mentioned options
         check                = checks the current status of the options above on a VM

QUANTITY : number of VMs the ACTION should apply to
           e.g.: ACTION=notonthefly, QUANTITY=5 then on the *first 5 VMs that are currently set to use* untar-on-the-fly untar-on-the-fly gets disabled

FILE : file that contains the IP addresses of all VMs on the cloud

example: ./changegfalfs.sh disable 20 cc-west-b.ip


## checkjobs-belle.sh

A tool that compares the current number of Belle-II payload jobs against the number of running condor jobs.
If the number of payload jobs is different to the number of running condor jobs, then it will output in 1 line per VM:
- the number of running payload jobs
- the number of running condor jobs
- the IP address
- the job slot that doesn't run a payload job

usage: ./checkjobs.sh FILE DEFAULTNUMBER

FILE          : file that contains the IP addresses of all VMs on the cloud

DEFAULTNUMBER : number of payload jobs that should run on the VM

example: ./checkjobs.sh cc-west-b.ip 8


## checkjobs-atlas.sh

Same as checkjobs-belle.sh, but checks for Atlas payload jobs.


# ganglia-belle.sh

Reports the usage statistics for the whole cloud to a ganlia server. To use it, the machine where it runs must be configured to report to a central Ganglia server and it must have gmetric installed.

The report includes:
basf2_jobs  :  number of Belle-II payload jobs
filler_jobs :  number of filler jobs when no payload was found
all_jobs    :  number of running condor jobs
CPUs        :  number of CPUs in all used VMs on the cloud
basf2_ratio :  basf2_jobs/all_jobs * 100 
filler_ratio:  filler_jobs/all_jobs * 100
condor_ratio:  all_jobs/CPUs * 100


usage: ./ganglia-belle.sh FILE

FILE : file that contains the IP addresses of all VMs on the cloud



## network-ganglia.sh

On a machine that is used as data server for Belle-II, it reports the data amount transferred out from last midnight to the current time to a ganglia server and it must have gmetric installed .
Statistics are reset to 0 each midnight.
To use it, the machine where it runs must be configured to report to a central Ganglia server.

usage: ./network-ganglia.sh



