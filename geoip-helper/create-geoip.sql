drop table if exists geoip;

create table geoip (
	start_ip decimal(39,0) not null, 
	end_ip decimal(39,0) not null, 
	continent_code varchar(255), 
	continent varchar(255), 
	country_code varchar(255), 
	country varchar(255), 
	city varchar(255), 
	region varchar(255), 
	latitude double not null, 
	longitude double not null,
	primary key (start_ip, end_ip)
);

load data local infile '/root/production-helpers/geoip-helper/geoip_db.csv'
into table geoip
fields terminated by ','
lines terminated by '\n'
ignore 1 rows
(start_ip, end_ip, continent_code, continent, country_code, country, city, region, latitude, longitude);
