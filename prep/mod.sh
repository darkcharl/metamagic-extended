#!/usr/bin/env bash

for f in $(ls -f orig/{Shared,SharedDev,Gustav,GustavDev}/*.txt); do
  echo "------------------------------------------------------------------------------------"
  echo -e " *** Processing: $f ***\n" 
  ./prep.py $f
  echo "------------------------------------------------------------------------------------"
  sleep 1
done
