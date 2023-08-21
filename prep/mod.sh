#!/usr/bin/env bash

# Clean old
rm modded/*.txt

# Run mod
./metamod.py extend

# Combine into single file for packaging
cat modded/Spell_*.txt > Spell_Metamagic.txt
