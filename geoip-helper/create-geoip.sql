drop table if exists geoip;

create table geoip (start_ip varchar(255), end_ip varchar(255), continent_code varchar(255), continent varchar(255), country_code varchar(255), country varchar(255), city varchar(255), region varchar(255), latitude double, longitude double);

load data local infile '/root/heprc/production-helpers/geoip-helper/geoip_db.csv'
into table geoip
fields terminated by ','
lines terminated by '\n'
ignore 1 rows
(start_ip, end_ip, continent_code, continent, country_code, country, city, region, latitude, longitude);
