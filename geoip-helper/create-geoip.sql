drop table if exists geoip;

create table geoip (ip_range varchar(255), continent_code varchar(255), continent varchar(255), country_code varchar(255), country varchar(255), city varchar(255), region varchar(255), region_code varchar(255), latitude double, longitude double, loc_acc_radius varchar(255));

load data local infile '/root/heprc/tail_geoip.csv'
into table geoip
fields terminated by ','
lines terminated by '\n'
ignore 1 rows
(ip_range, continent_code, continent, country_code, country, city, region, region_code, latitude, longitude, loc_acc_radius);

alter table geoip 
drop column country_code, drop column country, drop column region_code, drop column loc_acc_radius;

alter table geoip
add column start_ip bigint first, add column end_ip bigint after start_ip;

-- for IPv4 addresses: (if '.' is present as opposed to ':')
--insert 2 columns with integer ip addresses (start and end)

create table ipv4_conversion(ip_range varchar(255), temp_ip varchar(255), prefix_len int, ip_1 int, ip_2 int, ip_3 int, ip_4 int);
insert into ipv4_conversion (ip_range) select ip_range from geoip where instr(ip_range, '.')!=0;
update ipv4_conversion
set
temp_ip = ip_range,
prefix_len = convert(substring_index(temp_ip, '/', -1), int),
ip_1 = convert(substring_index(temp_ip, '.', 1), int),
temp_ip = substring(temp_ip, instr(temp_ip, '.')+1),
ip_2 = convert(substring_index(temp_ip, '.', 1), int),
temp_ip = substring(temp_ip, instr(temp_ip, '.')+1),
ip_3 = convert(substring_index(temp_ip, '.', 1), int),
temp_ip = substring(temp_ip, instr(temp_ip, '.')+1),
ip_4 = convert(substring_index(temp_ip, '/', 1), int);

update geoip as t1 natural join ipv4_conversion as t2
set t1.start_ip = t2.ip_1 * power(256, 3) + t2.ip_2 * power(256, 2) + t2.ip_3 * 256 + t2.ip_4;

update geoip as t1 natural join ipv4_conversion as t2
set t1.end_ip = power(2, 32 - t2.prefix_len) - 1 + start_ip;

drop table if exists ipv4_conversion;
alter table geoip drop column ip_range;

select * from geoip;
