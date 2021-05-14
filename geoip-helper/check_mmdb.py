#!/usr/bin/env python3

import geoip2.database

ip = '2001:4860:4860::8888' #'62.18.255.1'
with geoip2.database.Reader('./dbip.mmdb') as reader:
    response = reader.city(ip)

    print(response.country.name,
    response.city.name,
    response.subdivisions.most_specific.name,
    response.location.latitude,
    response.location.longitude)
