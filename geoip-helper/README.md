Start with conversion of mmdb file to csv. Change path/file names within mmdb_to_csv.py as needed.

For create-geoip.sql, must load a csv file of geodata in the following format of 10 columns:
start ip, end ip, continent code, continent, country code, country, city, region, latitude, longitude
Where the start/end IPs are in integer format.

Using MariaDB, with an existing database created, load in the sql file:
mysql <database_name> < create-geoip.sql
