### Guide to host management (Ganglia + Nagios)

####  UVic HEP Research Computing
##### Victor Kamel (Coop)

------

#### Background

Nagios is only aware of hosts that are explicitly specified in config files. However, Ganglia is able to dynamically add and remove hosts from its monitoring system. In addition, the Nagios service must be restarted for new config files to take effect. Therefore, I have developed a set of tools to make the process of syncing hosts from Ganglia to Nagios easier and more automated.

### Adding hosts to Nagios

Hosts can be added from the web interface. Click to the hosts tab on the left navigation bar, and you should get a list of current hosts. Next to the `localhost` host, there is a "Extra Host Notes" button (icon is a piece of paper) that can be clicked to open a custom web page. There is a link to add new hosts from Ganglia on this page.

When this link is clicked, the `/usr/local/nagios/etc/scripts/add_host.sh` is run. It will query the ganglia server for a list of actively monitored hosts. The config files for the hosts in Nagios are located in `/usr/local/nagios/etc/objects/hosts`. If Ganglia reported a host that is not in the `hosts` folder, a new config file will be created based on the configuration directory (see [Managing host config files](#managing-host-config-files)). Running this script only adds a new host if it is not currently in Nagios. It will neither remove hosts nor change their configuration.

Finally, the Nagios process is restarted so that the changes can take effect. Nagios will then automatically schedule service checks for the new hosts over the next few minutes (it doesn't check everything at once, active checks are staggered). To get results faster, clicking the service in the "Services" tab in the left navigation pane will lead you to a page where you can re-schedule any individual service check (the "Re-schedule the next check if this service" link on the right hand side of the window, under "Service Commands").


### Managing host config files

The configuration directory structure is located in `/etc/nagios/configurations`. Here is a sample directory structure.
```shell
configurations/
├── heprc.uvic.ca
│   ├── bellecs.cfg
│   ├── csv2a.cfg
│   ├── csv2.cfg
│   ├── default.cfg
│   └── dynafed02.cfg
├── other
│   └── default.cfg
└── phys.uvic.ca
    └── default.cfg
```

Inside the root directory (`configurations`), there are folders for domains. Inside each domain name there is a `default.cfg` file, along with `<hostname>.cfg` for different monitored hosts. In addition, there is an extra folder `other` that contains its own `default.cfg`.

When Nagios is adding a host from Ganglia (using my `add_host.sh` script), it uses this directory structure to determine how to configure it. There are several possible scenarios that can occur:

1. **Nagios detects a host that is unknown** (its domain is not in the configurations folder). Nagios will therefore apply the `other/default.cfg` config file.

2. **Nagios detects a host with a known domain only** (its domain is in the configuration folder, but there is no bespoke `<hostname>.cfg` present). Nagios will apply the `<domain>/default.cfg` config file.

3. **Nagios detects a known host** (its domain is in the configuration folder and there is a `<hostname>.cfg` present). Nagios will first apply `<domain>/default.cfg` THEN `<domain>/<hostname.cfg>`.

#### Structure of the config files

Config can have two sections:

##### The `[PROCESS]` section:
This section is a list (one per line) of all of the processes that need to be monitored (i.e. `X_service_running` metrics in Ganglia). Each process listed here be added to the config for this host automatically (derived from the `process_srvc.templ` template).

- If the process is running, the status of the service will be <span style="background-color:#88d066">OK</span>.
- If the process is not running, the status of the service will be <span style="background-color:#f88888">CRITICAL</span>.
- If this is not a valid process for the host, the status of the host will be <span style="background-color:#ffbb55">UNKNOWN</span>.

Example:
```shell
[PROCESS]
sshd
condor_poller
WorkloadManagement_SiteDirectorUVic
WorkloadManagement_SiteDirectorUVic2
WorkloadManagement_SiteDirectorUVic3
Framework_SystemAdministrator
WorkloadManagement_CountPilotSubmission
WorkloadManagement_B2CountPilotSubmission
condor_master
```

##### The `[COMMAND]` section:
This section is for adding other Nagios alerts. The format is as follows:
```shell
<metric>!<operator>!<critical_value> Name of service
``` 
For example, if I wanted an alert when the disk usage went above 90, I would add the following line:
```shell
part_max_used!more!90 Disk Usage
```

Example:
```shell
[COMMAND]
part_max_used!more!90 Disk Usage
Swap_Usage!more!50 Swap Usage
Unknown_SSH_Connections!notequal!0 Foreign SSH Connections
```

Note: To make deployment and configuration as simple as possible, this `configuration` directory structure should be synced with the deployment server. The deployment script is able to parse out Nagios config information and send only what is necessary to the monitored hosts.

### Removing hosts from Nagios

Hosts can be removed by 2 methods:

1. **Removing the host from the web interface.** Navigate to the "Hosts" or "Services" tab using the left navigation pane in Nagios, click the "Extra Host Actions" button (looks like a graph) next to the host that you want to remove. Click the "Remove this host from Nagios" link. This will remove the host and restart Nagios automatically. Note that if this host is still registered with Ganglia, it will be added back if you ever run the "Add hosts from Ganglia" script.

2. **Removing the host directly from the filesystem.** Remove the appropriate `<hostname>.cfg` from `/usr/local/nagios/etc/objects/hosts` and restart Nagios (`systemctl restart nagios`).

### Customizing Nagios Services

When a host is added, its config file is generated based on the `configurations` directory as well as the templates (`generic_host.templ`, `generic_srvc.templ` and `process_srvc.templ`). These templates make use of the `ganglia-linux-host` and `ganglia-service` objects defined in `/usr/local/nagios/etc/objects/ganglia_templates.cfg`. Therefore, to change the number of times that services are checked, the interval between the checks, etc. this is where those configurations are.
