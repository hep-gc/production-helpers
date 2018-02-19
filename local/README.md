# Installation

These scripts need to be in $HOME on a machine that has ssh access to cloudscheduler as well as to a machine that can reach all VMs on a cloud.
On the cloudscheduler machine, the tools from the cloudscheduler-directory need to be installed.
On the machine that has access to VMs of a cloud, the tools from the cloud-directory need to be installed.

In $HOME for the user, .ssh/config needs to have accesspoints to the cloud VMs be configured.
The different sections for the different clouds	should look like:

HOST cc-west-b
  user root
  hostname DNS-HOSTNAME                      
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  LogLevel quiet
  ForwardAgent yes

IMPORTANT: The identifier after	HOST in	the first line needs to	be the same name like the cloud-name configured	in cloudscheduler.
         

# Description

## changeVMs.sh

Script that can be used to increase the usage of a cloud. 
It will change the number of running VMs up to a maximum with a given increment per interval, only increasing the number of VMs if the VMs started in the previous interval all running payload, otherwise it will wait until they run payloads.

Note: VO, cloudscheduler machine, and ssh port are configured static within at the top


usage: ./changeVMs.sh CLOUD  CPUs MAXAMOUNT IPSTRING INCREMENT SLEEPTIME

                                                        
CLOUD : name of the cloud information is wanted for
        needs to be same name as defined in cloudscheduler

CPUs : number of how many CPUs a VM on that cloud has
       e.g. CPUs=8 when running 8-core VMs
       
MAXAMOUNT : max number of VMs that should run through a specific cloudscheduler on CLOUD

IPSTRING : identifier for the IPs on that cloud to identify VMs that are not reachable

INCREMENT : amount by which the number of VMs is increased per interval

SLEEPTIME : time to wait until the number of VMs is increased again


example: ./changeVMs.sh cc-west-b 8 "10.39" 5 10
         On cc-west-b the usage will be increase by 5 VMs every 10min, if the 8-core VMs started in the previous cycle are already running payload(basf2), 
         otherwise it will sleep for 10 min and check again. It will also wait with increasing the number of VMs if there are not enough idle jobs in the queue. 
         VMs on cc-west-b are identified by IPs starting with "10.39" and these machines that are not reachable get removed in the next cycle of the script.

          
          

## checkVMstatus.sh

Script that checks how many VMs do not run the maxium amount of payloads possible on it. 
It gets a list of IPs for currently running VMs on a cloud from the machine where cloudscheduler runs, transfers it to the machine that can access VMs on a cloud, and then let this machine check all the VMs.
For VMs that do not run payload on all job slots, it will give out in 1 line per VM:
- the number of running payload jobs
- the number of running condor jobs
- the IP of the VM
- the job slots that do not run a payload

Note: VO, cloudscheduler machine, and ssh port are configured static within at the top


usage: ./checkVMtatus.sh CLOUD CPUs

CLOUD : name of the cloud information is wanted for
        needs to be same name as defined in cloudscheduler
        
CPUs : number of how many CPUs a VM on that cloud has
       e.g. CPUs=8 when running 8-core VMs

example: ./checkVMstatus.sh cc-west-b 8

