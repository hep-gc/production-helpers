#!/bin/bash

curl "https://download.db-ip.com/free/dbip-city-lite-2021-06.mmdb.gz" | gunzip > city.mmdb
echo "Database download complete"

echo "Converting mmdb to csv..."
./mmdb_to_csv.py "city.mmdb"
rm city.mmdb
echo "MaxMind database converted to CSV"

echo "Splitting csv..."
./split_csv.py "geoip_db.csv"
rm geoip_db.csv
echo "CSV file split into IPv4 and IPv6"

echo "Creating SQL database..."
mysql -u root --password= -e "drop database if exists geoip; create database geoip;"
mysql -u root --password= geoip < geodata.sql
rm ipv4.csv
rm ipv6.csv
echo "SQL database created"

mysql -u root --password= geoip < geodata_updates.sql
echo "Updated MySQL data entires"

echo "Done"
