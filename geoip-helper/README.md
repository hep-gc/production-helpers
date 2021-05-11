For create-geoip.sql, must load a csv file of geodata in the following format:
ip_range, continent_code, continent, country_code, country, city, region, region_code, latitude, longitude, location_accuracy_radius
There must be 11 different types of data in each line, but 4 of them (country_code, country, region_code, location_accuracy_radius) can be empty as they will be removed.

Using MariaDB, with an existing database created, use the command:
mysql <database_name> < create-geoip.sql
