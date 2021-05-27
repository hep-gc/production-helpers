Start with conversion of mmdb file to csv. Pass in mmdb file as a command line argument: `./mmdb_to_csv 'filename.mmdb'`. Ouput goes to 'out.csv'.

Split the csv into two files: ipv4.csv and ipv6.csv.
* `./split_csv.py 'out.csv'`

For create-geoip.sql, must have 2 csv files of geodata (ipv4.csv and ipv6.csv) in the following format of 10 columns:
* start ip, end ip, continent code, continent, country code, country, city, region, latitude, longitude
  * (Where the start/end IPs are in integer format.)

Using MariaDB, with an existing database created, load in the sql file:
`mysql <database_name> < create-geoip.sql`

Query this database with an IP address:
* `select * from ipv4 where end_ip >= x order by end_ip asc limit 1;`
  * (Where x is the IPv4 address.)

* `select * from ipv6 where end_ip >= y order by end_ip asc limit 1;`
  * (Where y is the IPv6 address in integer format.)