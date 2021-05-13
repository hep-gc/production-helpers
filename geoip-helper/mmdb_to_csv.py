#!/usr/bin/env/ python3
"""
Original file is located at
    https://colab.research.google.com/drive/10OqsF-HPQ3ZltsV-DZ868bWJ49ceUPa5
"""

path = "/root/heprc/production-helpers/geoip-helper/"

import maxminddb
import copy
import pandas as pd

from ipaddress import IPv4Network, IPv6Network


def iterable(self):
    
    if self._metadata.ip_version == 4:
        start_node = self._start_node(32)
        start_network = IPv4Network((0, 0))
    else:
        start_node = self._start_node(128)
        start_network = IPv6Network((0, 0))

    search_nodes = [(start_node, start_network)]
    while search_nodes:
        node, network = search_nodes.pop()

        if network.version == 6:
            naddr = network.network_address
            if naddr.ipv4_mapped or naddr.sixtofour:
                # skip IPv4-Mapped IPv6 and 6to4 mapped addresses, as these are
                # already included in the IPv4 part of the tree below
                continue
            elif int(naddr) < 2 ** 32 and network.prefixlen == 96:
                # once in the IPv4 part of the tree, switch to IPv4Network
                ipnum = int(naddr)
                mask = network.prefixlen - 128 + 32
                network = IPv4Network((ipnum, mask))
        
        
        subnets = list(network.subnets())
        for bit in (0, 1):
            next_node = self._read_node(node, bit)
            subnet = subnets[bit]

            if next_node > self._metadata.node_count:
                data = self._resolve_data_pointer(next_node)
                # Code to output start/end IPs as integers
                start_ip = int(subnet.network_address)
                range = int((str(subnet).split('/'))[1])
                if network.version == 4:
                  addr_len = 32
                else:
                  addr_len = 128
                end_ip = start_ip + 2 ** (addr_len - range) - 1
                yield (start_ip, end_ip, data)
            elif next_node < self._metadata.node_count:
                search_nodes.append((next_node, subnet))

"""Input the file name"""

input_file = 'dbip.mmdb'

output_file = 'test.csv'

counter=0
write_header = True

# Change: removed 'range', 'region_code', 'location_accuracy_radius', and added 'start_ip', 'end_ip'
row_format = {
  'start_ip': "",
  'end_ip': "",
  'continent_code': "",
  'continent': "",
  'country_code': "",
  'country': "",
  'city': "",
  'region': "",
  'latitude': None,
  'longitude': None,
  'hash': "",
}

out_file = path + output_file

with maxminddb.open_database(path + input_file) as reader:

  rows = []
  count = 0
  for node in iterable(reader):
    if count >= 10:
      break
    count += 1

    row = copy.deepcopy(row_format)
    
    row['start_ip'] = node[0]
    row['end_ip'] = node[1]

    d = node[2]

    if 'continent' in d:
      if 'code' in d['continent']:
        row['continent_code'] = d['continent']['code']

      if 'names' in d['continent']:
        if 'en' in d['continent']['names']:
            row['continent'] = d['continent']['names']['en']
    
    # Change: 'registered_country' to 'country'
    if 'country' in d:
      if 'iso_code' in d['country']:
          row['country_code'] = d['country']['iso_code']

      if 'names' in d['country']:
        if 'en' in d['country']['names']:
            row['country'] = d['country']['names']['en']
    
    if 'city' in d:
      if 'names' in d['city']:
          if 'en' in d['city']['names']:
            row['city'] = d['city']['names']['en']

            
    
    if 'subdivisions' in d:
      if 'names' in d['subdivisions'][0]:
          if 'en' in d['subdivisions'][0]['names']:
            row['region'] = d['subdivisions'][0]['names']['en']

    if 'location' in d:
      if 'latitude' in d['location']:
        row['latitude'] = d['location']['latitude']

      if 'longitude' in d['location']:
        row['longitude'] = d['location']['longitude']

    if 'longitude' in d:
      row['longitude'] = d['longitude']

    row['hash'] = hash(row['city']+str(row['latitude'])+str(row['longitude']))
    
    counter += 1
    rows.append(row)
    
    if counter % 10000 == 0:
      # Iterate through sorted list of row dicts, compare side-by-side entries, combine when possible
      rows.sort(key=lambda i: i['start_ip'])
      length = len(rows)
      i = 0
      while i < length-1:
        if rows[i]['hash'] == rows[i+1]['hash']:
          if rows[i]['end_ip']+1 == rows[i+1]['start_ip']:
            rows[i]['end_ip'] = rows[i+1]['end_ip']
            rows.remove(rows[i+1])
            length = len(rows)
          elif rows[i]['start_ip']-1 == rows[i+1]['end_ip']:
            rows[i]['start_ip'] = rows[i+1]['start_ip']
            rows.remove(rows[i+1])
            length = len(rows)
          else:
            i = i + 1
        else:
          i = i + 1
      for row in rows:
        del row['hash']

      pd.DataFrame(rows).to_csv(out_file, mode='a', header=write_header, index=False)
      write_header = False
      rows = []
      print('.',end='')
    
    if counter % 1000000 == 0:
      print('.')
    
# Ouput final list of rows
rows.sort(key=lambda i: i['start_ip'])
length = len(rows)
i = 0
while i < length-1:
  if rows[i]['hash'] == rows[i+1]['hash']:
    if rows[i]['end_ip']+1 == rows[i+1]['start_ip']:
      rows[i]['end_ip'] = rows[i+1]['end_ip']
      rows.remove(rows[i+1])
      length = len(rows)
    elif rows[i]['start_ip']-1 == rows[i+1]['end_ip']:
      rows[i]['start_ip'] = rows[i+1]['start_ip']
      rows.remove(rows[i+1])
      length = len(rows)
    else:
      i = i + 1
  else:
    i = i + 1
for row in rows:
  del row['hash']

pd.DataFrame(rows).to_csv(out_file, mode='a', header=False, index=False)

