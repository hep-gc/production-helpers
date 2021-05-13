For create-geoip.sql, must load a csv file of geodata in the following format of 10 columns:
start ip, end ip, continent code, continent, country code, country, city, region, latitude, longitude
Where the start/end IPs are in integer format.

Using MariaDB, with an existing database created, use the command:
mysql <database_name> < create-geoip.sql
