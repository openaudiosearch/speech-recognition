#!/usr/bin/env python3

# Copyright  2021  Ewald Enzinger

import sys

if len(sys.argv) != 3:
    print("Insufficient arguments! Usage: prepare_lexicon.py grapheme_lexicon lexicon.txt")
    sys.exit(1)

lexicon = {}
with open(sys.argv[1], 'r', encoding='utf-8') as grapheme_lexicon_file:
    for line in grapheme_lexicon_file:
        line = line.strip()
        lexicon[line] = " ".join([char for char in list(line)])

print(f"{len(lexicon.keys())} lexicon entries!")

with open(sys.argv[2], 'w', encoding='utf-8') as lexicon_file:
    for key in sorted(lexicon.keys()):
        lexicon_file.write(f"{key}  {lexicon[key]}\n")
