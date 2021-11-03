<?php
$conf['gweb_root'] = dirname(dirname(__FILE__));

include_once $conf['gweb_root'] . "/eval_conf.php";
include_once $conf['gweb_root'] . "/functions.php";
include_once $conf['gweb_root'] . "/lib/common_api.php";

# Set appropriate context
if ( isset($_GET['action']) ) {
	switch ( $_GET['action'] ) {
		case 'list_grids'   : $context = 'meta'   ; break;
		case 'list_clusters': $context = 'grid'   ; break;
		case 'list_hosts'   : $context = 'cluster';
	}

	$target = explode("_", $_GET['action'])[1];

} else { $context = 'cluster'; }

# Adds granularity to list results
if ( isset($_GET['grid'   ]) ) $gridname    = $_GET['grid'   ];
if ( isset($_GET['cluster']) ) $clustername = $_GET['cluster'];
if ( isset($_GET['host'   ]) ) $hostname    = $_GET['host'   ];

include_once $conf['gweb_root'] . "/functions.php";
include_once $conf['gweb_root'] . "/ganglia.php";
include_once $conf['gweb_root'] . "/get_ganglia.php";

header("Content-Type: text/json");

# Alias `metrics` parameter to `metric`
if ( isset($_GET['metric']) ) $_GET['metrics'] = $_GET['metric'];

# Handle list actions
if ( isset($target) ) {

	if ($target == 'hosts') { $ret = array_keys($metrics); }
	else {
		switch ($target) {
			case 'grids'   : $filter = function ($x) { return array_key_exists('GRID',    $x) && ($x['GRID']    == 1) ; }; break;
			case 'clusters': $filter = function ($x) { return array_key_exists('CLUSTER', $x) && ($x['CLUSTER'] == 1); };
		}

		$ret = array();
        	foreach ($grid as $name => $source)
        		if ( $filter($source) ) $ret[] = $name;
	}

	api_return_ok(array($target => $ret));

# Handle requests for data
} elseif ( isset($clustername)     &&    # Cluster name
           isset($hostname)        &&    # Host name
           isset($_GET['metrics']) &&    # Metric name
           isset($_GET['start_e']) &&    # Start time (epoch)
           isset($_GET['end_e'])   &&    # End time (epoch)
           isset($_GET['res'])        ){ # Data resolution

	$start       = $_GET['start_e'];
	$end         = $_GET['end_e'];
	$resolution  = $_GET['res'];

	$ret = array();

	foreach (explode(',', $_GET['metrics']) as $metricname) {	
		
		# Check that the user requested a valid metric.
		if ( ! array_key_exists($metricname, $metrics[$hostname]) ) api_return_error("Invalid metric " . $metricname . " for host " . $hostname);

		$command  = $conf['rrdtool'] . " fetch -a ";
		$command .= $conf['rrds'] . "/'$clustername'/$hostname/$metricname.rrd";
		$command .= " -r $resolution -s $start -e $end AVERAGE" . " 2>&1";

		$output = null;
		$res = null;
		exec($command, $output, $res);
	
		if ($res == 0) {
			$ret[$metricname] = array_map(function ($x) { return explode(": ", $x); }, array_slice($output, 3));
		} else { api_return_error($output); }
	}

	api_return_ok($ret);

# User did not provide appropriate parameters
} else { api_return_error("You need to supply an action or the cluster, host, metric, start_e, end_e and res."); }

?>
