#!/usr/bin/env bash

# Clean old
rm modded/*.txt

# Create variants
for f in $(ls -f orig/{Shared,SharedDev,Gustav,GustavDev}/*.txt); do
  echo "------------------------------------------------------------------------------------"
  echo -e " *** Processing: $f ***\n" 
  ./prep.py $f
  echo "------------------------------------------------------------------------------------"
  #sleep 1
done

# Combine into single file for packaging
cat modded/Spell_*.txt > Spell_Metamagic.txt
