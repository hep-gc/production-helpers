#!/usr/bin/env python3

import sys
import sqlgeoip

ip = sys.argv[1]

reader = sqlgeoip.Reader("geoip")
r = reader.city(ip)

print(r.city.name, r.country.name, r.country.iso_code,
      r.continent.name, r.continent.code, r.subdivisions.most_specific.name,
      r.location.latitude, r.location.longitude)

