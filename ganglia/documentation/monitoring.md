### Guide to setting up a monitoring server (Ganglia + Nagios) on Centos 7/8

####  UVic HEP Research Computing
##### Victor Kamel (Coop)

```
NOTES
- Server must allow TCP ingress on port 80 (HTTP).
- Server must allow UDP ingress on port 8649 (gmond).
- After completing these steps and ensuring that everything is working, deploy monitoring to this host (not covered here).
- The following must be updated in the gmond.conf deployed to monitored servers
  i)  The cluster name in the cluster block
  ii) The host IP in the udp_send_channel block
- Further configuration will be required to enable notifications.
```

####Tentative hardware requirements:

- 8 GB RAM
- 4 CORES
- 100 GB DISK

-------

### Install Ganglia

0. Become root (`sudo su -`).

1. Installing ganglia packages
Install packages:
```sh
yum update && yum install epel-release
yum install rrdtool rrdtool-devel ganglia-web ganglia-gmetad ganglia-gmond httpd httpd-tools apr-devel zlib-devel libconfuse-devel expat-devel pcre-devel php-xml
```

2. Edit `/etc/ganglia/gmetad.conf`  
<span style="color:red">(–) `data_source "my cluster" localhost`</span>  
<span style="color:green">(+) `data_source "<cluster name>" localhost`</span>  
<span style="color:green">(+) `gridname "<grid name>"`</span>


3. Edit `/etc/ganglia/gmond.conf`  
<span style="color:red">(–) `send_metadata_interval = 0 /*secs */`</span>  
<span style="color:green">(+) `send_metadata_interval = 60 /*secs */`</span>  
<br>
And ensure the following configuration:  
```
cluster {
  name = "<cluster name>"
  owner = "unspecified"
  latlong = "unspecified"
  url = "unspecified"
}

host {
  location = "unspecified"
}

udp_send_channel {
  host = <ip of localhost>
  port = 8649
  ttl = 1
}

udp_recv_channel {
  port = 8649
}

tcp_accept_channel {
  port = 8649
}
```

4. Create user for accessing ganglia
```sh
htpasswd -c /etc/httpd/auth.basic <user>
```

5. Add Ganglia to httpd for remote access
```sh
$ vim /etc/httpd/conf.d/ganglia.conf

Alias /ganglia /usr/share/ganglia

<Location /ganglia>
  AuthType basic
  AuthName "Ganglia Server"
  AuthBasicProvider file
  AuthUserFile "/etc/httpd/auth.basic"
  Require user <user>
</Location>
```

6. Disable ganglia authorization
```sh
$ vim /etc/ganglia/conf.php

$conf['auth_system'] = 'disabled';
```

7. Move custom ganglia files to this server  

- Create new directory `/usr/share/ganglia/dev`.
- Move `ganglia/request.php` (local) to directory `/usr/share/ganglia/dev` (remote).

8. Restart/enable all services
```sh
systemctl restart httpd
systemctl restart gmond
systemctl restart gmetad
systemctl enable httpd
systemctl enable gmond
systemctl enable gmetad
```

#### Troubleshooting steps (Ganglia)

```sh
# Ensure that ganglia ca write to rrds files
chown -R ganglia:ganglia /var/lib/ganglia/rrds

# Try to disable SELinux
$ vim /etc/sysconfig/selinux
SELINUX=disabled
$ reboot

# Commands to view gmond log
cat /var/log/messages | grep "gmond"
gmond -d 1

# Change httpd LogLevel to error
$ vim /etc/httpd/conf/httpd.conf
LogLevel error
```

-------

### Install Nagios

0. Become root (`sudo su -`).

1. Install Nagios Core / Nagios Plugins  
Follow instructions [here](https://support.nagios.com/kb/article/nagios-core-installing-nagios-core-from-source-96.html#CentOS) to install Nagios Core & Nagios Plugins from source.

2. Edit `/etc/httpd/conf.d/nagios.conf` in the `/usr/local/naigos/share` directory `version >= 2.3`. Use the username that you set in the steps above.  
<span style="color:red">(–) `valid-user`</span>  
<span style="color:green">(+) `user <username>`</span>  

3. Edit `/usr/local/nagios/etc/nagios.cfg`  
<span style="color:green">(+) `cfg_file=/usr/local/nagios/etc/objects/ganglia_templates.cfg`</span>  
<span style="color:green">(+) `cfg_dir=/usr/local/nagios/etc/objects/hosts`</span>  
Ensure that `check_external_commands` is set to `1`.

4. Edit `/usr/local/nagios/etc/cgi.cfg`. Set `action_url_target` and `notes_url_target` to `_self`. 

5. Move custom configurations/scripts over to server

- Create new directory `/usr/local/nagios/etc/objects/hosts` with `apache:apache` ownership.
- Create new directory `/usr/local/nagios/etc/scripts` with `nagios:nagios` ownership.
- Create new directory `/usr/local/nagios/share/hostctl`.
- Create new directory `/etc/nagios`.
- Move `nagios/ganglia_templates.cfg` to `/usr/local/nagios/etc/objects`.
- Move `nagios/localhost.cfg` to `/usr/local/nagios/etc/objects`.
- Move everything in `nagios/scripts` to `/usr/local/nagios/etc/scripts`.
- Move everything in `nagios/web` to `usr/local/nagios/share/hostctl`.
- Rsync (`rsync -crpz `) `../scripts/current/configurations` with `/etc/nagios` on the remote server.
- Add netrc file for Ganglia (replace `<user>` and `<password>` with login information for Ganglia)
```sh
$ vim /usr/local/nagios/etc/scripts/ganglia_rc
machine localhost login <user> password <password>
```
```
NOTE
- If the Ganglia server was not set up with a administrator user/password, this step
  should be skipped and the --netrc-file /usr/local/nagios/etc/scripts/ganglia_rc
  option should be removed from the curl command on line 34 in both check_heartbeat.sh
  and check_ganglia_metric.sh
```
5. Restart Nagios / httpd
```sh
systemctl restart nagios
systemctl restart httpd
```

#### Troubleshooting steps (Nagios)

**Note:** Nagios will fail to start if there is an error in the configuration.

```sh
# Check nagios config file integrity
/usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg

# Check nagios log
less /usr/local/nagios/var/nagios.log

# Check systemd journal if nagios service fails to start
journalctl
```