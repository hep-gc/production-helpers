#!/usr/bin/env python3

import sys
import pandas as pd

filename = sys.argv[1]
df = pd.read_csv(filename, chunksize=10000)

write_header = True

for chunk in df:
   ipv4_rows = []
   ipv6_rows = []
   for index, row in chunk.iterrows():
      if int(row['start_ip']) < 4294967296:
         ipv4_rows.append(row)
      else:
         ipv6_rows.append(row)
   pd.DataFrame(ipv4_rows).to_csv('./ipv4.csv', mode='a', header=write_header, index=False)
   pd.DataFrame(ipv6_rows).to_csv('./ipv6.csv', mode='a', header=write_header, index=False)
   write_header = False
   print('.', end='')
