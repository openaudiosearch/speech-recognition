#!/usr/bin/env bash

# Copyright 2017 QCRI (author: Ahmed Ali)
#           2019 Dongji Gao
# Apache 2.0
# This script prepares the subword dictionary.

set -e
dir=data/local/dict
num_merges=1000

mkdir -p $dir

# Create grapheme lexicon
cat data/train/text |\
  awk '{for(n=2;n<=NF;n++) { if($n!="") {p[$n]=1; }}} END{for(x in p) {print x}}' |\
  sed -e "s/\[spoken-noise\]//g;s/\[noise\]//g;s/\[laughter\]//g;s/<unk>//g;s/-//g" |\
  sort >data/local/grapheme_lexicon

echo "$0: processing lexicon text and creating lexicon..."
local/prepare_lexicon.py data/local/grapheme_lexicon $dir/lexicon.txt

grep -v -w SIL $dir/lexicon.txt |\
  awk '{for(n=2;n<=NF;n++) { p[$n]=1; }} END{for(x in p) {print x}}' |\
  sort > $dir/nonsilence_phones.txt

echo UNK >> $dir/nonsilence_phones.txt
#echo LGN >> $dir/nonsilence_phones.txt

echo SIL > $dir/silence_phones.txt

echo SIL >$dir/optional_silence.txt

echo -n "" >$dir/extra_questions.txt

# Make a subword lexicon based on current word lexicon
glossaries="<unk> [noise] [spoken-noise] [laughter]"

echo "$0: making subword lexicon... $(date)."
# get pair_code file
cut -d' ' -f2- data/train/text | sed 's/\[noise\]//g;s/<unk>//g;s/\[spoken-noise\]//g;s/\[laughter\]//g' | python3 utils/lang/bpe/learn_bpe.py -s $num_merges > data/local/pair_code.txt
mv $dir/lexicon.txt $dir/lexicon_word.txt
# get words
cut -d ' ' -f1 $dir/lexicon_word.txt > $dir/words.txt
python3 utils/lang/bpe/apply_bpe.py -c data/local/pair_code.txt --glossaries $glossaries < $dir/words.txt | \
sed 's/ /\n/g' | sort -u > $dir/subwords.txt

python3 - $dir/subwords.txt >$dir/lexicon.txt << "EOF"
import sys
with open(sys.argv[1], 'r', encoding='utf-8') as vocab_file:
    for line in vocab_file:
        line = line.strip()
        if line == "[laughter]":
            pron = "SIL"
            #continue
        elif line == "[noise]":
            pron = "SIL"
            #continue
        elif line == "<unk>" or line == "[spoken-noise]":
            pron = "UNK"
        elif line == "<s>" or line == "</s>" or line == "-pau-" or line == "":
            continue
        else:
            pron = ' '.join(list(line))
        pron = pron.replace(" @ @", "")
        print(f"{line} {pron}")
EOF

sed -i '1i<unk> UNK' $dir/lexicon.txt
#echo '[noise] NSN' >> $dir/lexicon.txt
echo '[spoken-noise] UNK' >> $dir/lexicon.txt
#echo '[laughter] LGN' >> $dir/lexicon.txt

echo "$0: Dictionary preparation succeeded"
