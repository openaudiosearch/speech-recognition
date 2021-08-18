#!/usr/bin/env bash

# Copyright 2021  Ewald Enzinger

. path.sh || exit 1

locdata=data/local
locdict=$locdata/dict_nosp

echo "=== Preparing the dictionary ..."
mkdir -p $locdict

#LC_ALL=de_DE.UTF-8 awk '{n=split($1,a,""); printf("%s", $0); for(i=1;i<=n;i++){printf(" %s", a[i]);} printf("\n"); }' $locdata/vocab-full.txt >$locdict/lexicon.txt

python3 - $locdata/vocab-full.txt >$locdict/lexicon.txt << "EOF"
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as vocab_file:
    for line in vocab_file:
        line = line.rstrip("\n")
        if line == "[laughter]" or line == "[spoken-noise]":
            pron = "SPN"
        elif line == "<unk>":
            pron = "SIL"
        elif line == "<s>" or line == "</s>" or line == "-pau-":
            continue
        elif len(line) == 1:
            if line in ['b', 'c', 'd', 'g', 'j', 'p', 'q', 't', 'w']:
                pron = f"{line} e"
            elif line in ['f', 'l', 'm', 'n', 'r', 's']:
                pron = f"e {line}"
            elif line in ['h', 'k']:
                pron = f"{line} a"
            elif line == 'v':
                pron = 'f a u' 
            elif line == 'x':
                pron = 'i k s' 
            elif line == 'y':
                pron = 'ü p s i l o n'
            elif line == 'z':
                pron = 't s e t' 
            else:
                pron = line
        else:
            pron = ' '.join(list(line))
        pron = pron.replace("' ", "").replace(" '", "").replace("-", "")
        pron = pron.replace("s c h", "sch").replace("c h", "ch").replace("c k", "k")
        print(f"{line}\t{pron}")
EOF

echo "--- Preparing pronunciations for OOV words ..."

echo "--- Prepare phone lists ..."
echo SIL > $locdict/silence_phones.txt
echo SIL > $locdict/optional_silence.txt
grep -v -w SIL $locdict/lexicon.txt | \
  awk '{for(n=2;n<=NF;n++) { p[$n]=1; }} END{for(x in p) {print x}}' |\
  sort > $locdict/nonsilence_phones.txt

# Some downstream scripts expect this file exists, even if empty
touch $locdict/extra_questions.txt

echo "*** Dictionary preparation finished!"
