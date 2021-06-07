#!/bin/bash

checkIP()
{
 sleep 100
 ./test_sql.py "$((1 + $RANDOM % 100)).$((1 + $RANDOM % 200)).$((1 + $RANDOM % 100)).$((1 + $RANDOM % 100))"
}
for i in {0..100}
do
  checkIP &
done
echo sleeping
pkill sleep;
wait
