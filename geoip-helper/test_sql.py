#!/usr/bin/env python3

import sys
import mysql.connector
import ipaddress

mydb = mysql.connector.connect(
   host="localhost",
   user="root",
   password="",
   database="test_db"
)

#with mydb.cursor(dictionary=True) as cursor:
cursor = mydb.cursor(dictionary=True)
address = ipaddress.ip_address(sys.argv[1])
ip = int(address)
#if address.version == 4:
#   table = ipv4
#else:
#   table = ipv6

select = "SELECT * FROM ipv4 WHERE end_ip >= INET_ATON(%s) ORDER BY end_ip ASC LIMIT 1"
cursor.execute("SELECT * FROM ipv4 WHERE end_ip >= %d ORDER BY end_ip ASC LIMIT 1" % ip)

row = cursor.fetchone()
#print(ip,row)
if row is None or row['start_ip'] > ip:
   print("IP address is not database")
else:
   print(row)
