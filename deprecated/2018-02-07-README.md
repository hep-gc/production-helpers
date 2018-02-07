# Production Helpers

Scripts to ease the use of interactive processing environment. This repository
(production-helpers) was forked from "vm-helpers" and modified to integrate with
Cloud Scheduler (VM batch scheduler) and Repoman (image repository manager).

vm-kill                 - A script to shutdown and destroy interactive VMs.

vm-list                 - A script to list running VMs.

vm-run                  _ A script to instantiate a VM.


The following scripts all require a running MyProxy server to manage X509 proxy credentials
and require the user to set the MYPROXY_SERVER environment variable to indicate its URL.

cloud-bashrc            - A login script to be executed from the users .bachrc to query 
                          and renew local proxy certificates.

cloud-cernvm-setup      - Script to set up cloud environment in a base CernVM. The file
                          does not have execute permissions because it MUST be sourced, 
                          ie. ". cloud-cernvm-setup".

cloud-init              - Deprecated - replaced by cloud-myproxy-init.

cloud-logon             - An interactive version of cloud-bashrc. Issuing "cloud-logon -h"
                          provides detailed information on how to use the cloud-bashrc and
                          cloud-logon commands.

cloud-myproxy-init      - A script, usually called by the cloud-bashrc/cloud-logon, to
                          initialize X509 proxy credentials with a MyProxy server. The 
                          script must be accessible via the users PATH.

cloud-myproxy-logon     - A script, usually called by cloud-bashrc/cloud-logon, to renew
                          a users local proxy certificate from a MyProxy server.

QuerySetProxy           - Deprecated - replaced by cloud-bashrc/cloud-logon.
