<?php
$HOST_DIR='/usr/local/nagios/etc/objects/hosts';

if ( isset($_GET['host']) ) {
	$host = $_GET['host'];
} else {
	die("Must supply a host name");
}

if ( isset($_GET['action']) ) {
	$action = $_GET['action'];
	if ( $action === 'remove_host' ) {
                if ( unlink("{$HOST_DIR}/{$host}.cfg") ) {
			shell_exec('/usr/local/nagios/etc/scripts/restart_nagios.sh');
			echo "<h3><pre>Host has been removed.</pre></h3>";
		} else {
			echo "<h3><pre>Failed to remove host.</pre></h3>";
			echo '<a href="javascript:history.back()">Return</a>';
		}
	}
} else {
	echo '<a href="javascript:history.back()">Return</a>';
        echo "<h2> Action directory for host: <em>$host</em> </h2>";
        echo '<h3> Host configuration: </h3>';
        echo "1: <a href=?host=$host&action=remove_host> Remove this host from Nagios </a>";
}
?>


