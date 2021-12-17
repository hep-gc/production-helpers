<?php

if ( isset($_GET['action']) ) {
	$action = $_GET['action'];
	if ( $action === 'add_hosts' ) {
		$output = null;
		$res = null;
		exec('/usr/local/nagios/etc/scripts/add_hosts.sh', $output, $res);
		foreach ($output as $v) {
			echo "<h3><pre>$v</pre></h3>";
		}
		if ( $res === 1 ) {
			shell_exec('/usr/local/nagios/etc/scripts/restart_nagios.sh');
		}

		echo '<a href="javascript:history.back()">Return</a>';
	}
} else {
	echo '<a href="javascript:history.back()">Return</a>';
	echo '<h2> Action directory for host: <em>localhost</em> </h2>';
	echo '<h3> Ganglia: </h3>';
	echo "1: <a href=?action=add_hosts> Add new hosts from Ganglia </a>";
}

?>

