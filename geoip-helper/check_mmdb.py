#!/usr/bin/env python3

import sys
import geoip2.database

ip = sys.argv[1] #'2001:4860:4860::8888'
with geoip2.database.Reader('./dbip-city-lite-2021-05.mmdb') as reader:
    response = reader.city(ip)

    print(response.continent.code, response.continent.name, response.country.iso_code, response.country.name,
    response.city.name,
    response.subdivisions.most_specific.name,
    response.location.latitude,
    response.location.longitude)
