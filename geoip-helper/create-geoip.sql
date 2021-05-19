-- drop table if exists geoip;
drop table if exists ipv4;
-- drop table if exists ipv6;

/*
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
	longitude double not null
);
*/

create table ipv4 (
	start_ip int unsigned  not null, 
	end_ip int unsigned not null, 
	continent_code varchar(255), 
	continent varchar(255), 
	country_code varchar(255), 
	country varchar(255), 
	city varchar(255), 
	region varchar(255), 
	latitude double not null, 
	longitude double not null
);
-- primary key(start_ip, end_ip)

load data local infile './ipv4.csv'
into table ipv4
fields terminated by ','
lines terminated by '\n'
ignore 1 rows
(start_ip, end_ip, continent_code, continent, country_code, country, city, region, latitude, longitude);

create index start on ipv4(start_ip);
create index end on ipv4(end_ip);
/*
create table ipv4 (
	start_ip int unsigned  not null, 
	end_ip int unsigned not null, 
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
create table ipv6 (
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

insert into ipv4 select * from geoip where start_ip < 4294967296;
insert into ipv6 select * from geoip where start_ip >= 4294967296;

drop table if exists geoip;
*/
