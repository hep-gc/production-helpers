# @AUTHOR: Victor Kamel

import requests
from hashlib import md5

class GangliaAPI:
    """
    Extract data from Ganglia Monitoring Server.
    Server must have requestv2.php script at /ganglia/dev/requestv2.php.
    """
    
    def __init__(self, URL, auth=None):
        self.url  = URL  # URL of Ganglia Monitoring Server
        self.auth = auth # Tuple, (username, password)

    def _make_request(self, api, params):
        """
        Internal function for making a request to the API.
        """

        r = requests.get(self.url + api, auth=self.auth, params=params)

        # Error on failed request
        if r.status_code != 200: raise Exception(r)

        try:    return r.json()['message']
        except: return r.json()
        
    def get_hostnames(self):
        """
        Returns list of hostnames for the hosts registered on the ganglia server.
        """

        return set(self._make_request('dev/requestv2.php', {'action':'list_hosts'})['hosts'])
    
    def get_data(self, cluster, host, metrics, start, end, resolution):
        """
        Send data request to Ganglia Monitoring Server, returns received message.
        
        cluster: Name of cluster
        host:    Name of host
        metrics: Comma separated list of metrics to fetch
        start_e: Start date/time (unix timestamp or AT-Style time)
        end_e:   End date/time (unix timestamp or AT-Style time)
        res:     Data aggregation resolution (mean)
        """
        
        return self._make_request(
            'dev/requestv2.php', {
            "cluster" : cluster,
            "host"    : host,
            "metrics" : metrics,
            "start_e" : start,
            "end_e"   : end,
            "res"     : resolution
        })

    def get_events(self):
        """
        Returns list of events registered with the server.
        """

        return self._make_request('api/events.php', {'action':'list'})

    def add_event(self, start_time, end_time, summary, host_regex):
        """
        Add event with given parameters.
        """

        return self._make_request(
            'api/events.php', {
            'action'     : 'add',
            'start_time' : str(start_time),
            'end_time'   : str(end_time),
            'summary'    : summary,
            'host_regex' : host_regex
        })



    def remove_event(self, event_id):
        """
        Remove event by id.
        """
        
        return self._make_request(
            'api/events.php', {
            'action'  : 'remove',
            'event_id': event_id
        })

    def __repr__(self): return f"GangliaAPI({repr(self.url)}, {repr(self.auth)})"    # String repesentation of function
    def __str__(self):  return md5((self.url + str(self.auth)).encode()).hexdigest() # Hash of object as a string