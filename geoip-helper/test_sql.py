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

address = ipaddress.ip_address(sys.argv[1])
ip = int(address)
if address.version == 4:
   table = 'ipv4'
else:
   table = 'ipv6'

cursor = mydb.cursor(dictionary=True)
cursor.execute("SELECT * FROM %s WHERE end_ip >= %d ORDER BY end_ip ASC LIMIT 1" % (table, ip))

row = cursor.fetchone()
if row is None or row['start_ip'] > ip:
   print("IP address is not in database")
else:
   print(row)
