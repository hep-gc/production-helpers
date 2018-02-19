# Installation

These scripts need to be in $HOME on the machine that has cloudscheduler installed. The user must have sudo rights.

In $HOME for the user on the cloudscheduler machine, .ssh/config needs to have accesspoints to the cloud VMs be configured.
The different sections for the different clouds should look like:

HOST cc-west-b
  user root
  hostname DNS-HOSTNAME
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  LogLevel quiet
  ForwardAgent yes

IMPORTANT: The identifier after HOST in the first line needs to be the same name like the cloud-name configured in cloudscheduler.
  

To use the tools with Amazon, aws tools need to be installed. To do so as a user, one can do:
   pip install awscli --upgrade --user
and then add $HOME/.local/bin to $PATH

   Note: This installs a different version of python for aws which doesn't seem to be compatible with cloud_scheduler, resulting in cloud_status and
         cloud_admin to be no longer working
         To use cloud_status and cloud_admin again, one needs to install as user the new boto3 too:
         pip install boto3 --upgrade --user
         

# Description

## testqueue.sh

Tests if there are a minimum idle jobs available. If not then it waits until enough become available.
It's not to be used interactively, but by the tools in the local-directory.


## getinfo.sh

Give information about VMs on a specific cloud and can also perform actions on those.

NOTE: Currently not supporting Openstack API v3

usage: ./getinfo.sh CLOUD ACTION

                                                        
CLOUD : name of the cloud information is wanted from
        needs to be same name as defined in cloudscheduler

ACTION : different commands that can be used to get specific information or do something with a VM
         possible actions are:
           ip   : lists the IPs for all VMs on that cloud that are managed through the local cloudscheduler
           list : queries the cloud (Openstack or Amazon) for information about running VMs
                  includes ALL VMs on that cloud for the same tenant, no matter if managed through the local cloudscheduler or not
            NOTE: For Amazon VMs, the hostname for all running VMs in the region are given, no matter if managed through cloudscheduler or not      

           nova commands: Nova commands with 1 additional parameter can be given, e.g. "delete ID" to delete a specific VM
                          works only for clouds accessible through nova cli


examples: cloud=cc-west-b; ./getinfo.sh $cloud ip > $cloud.ip
          (it will generate the IP file needed by tools in the cloud-directory)

          cloud=cc-west-b; for i in $(./getinfo.sh $cloud list|grep -v ACTIVE|grep $cloud|cut -d" " -f 2); do ./getinfo.sh $cloud delete $i; done
          (gets the information about not-active VMs on $cloud, extracts the ID, and deletes those VMs from the cloud)
          
          cloud=cc-west-b; ./getinfo.sh $cloud flavor-list
          (lists all available flavors on $cloud)
          
          
