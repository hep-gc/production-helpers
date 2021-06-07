#!/bin/bash


for i in {0..100}
do
 ./test_classes.py "$((1 + $RANDOM % 100)).$((1 + $RANDOM % 200)).$((1 + $RANDOM % 100)).$((1 + $RANDOM % 100))"
done
