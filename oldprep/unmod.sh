#!/usr/bin/env bash

# Clean old
rm unmodded/*.txt

# Create variants
for f in $(ls -f orig/{Shared,SharedDev,Gustav,GustavDev}/*.txt); do
  echo "------------------------------------------------------------------------------------"
  echo -e " *** Processing: $f ***\n" 
  ./unprep.py $f
  echo "------------------------------------------------------------------------------------"
  #sleep 1
done

# Combine into single file for packaging
cat unmodded/Spell_*.txt > Spell_Metamagic_Restored.txt
