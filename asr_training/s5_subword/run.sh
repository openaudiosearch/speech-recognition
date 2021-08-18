#!/usr/bin/env bash

# Trainingspipeline, die ein Subwortlexikon auf Basis von Byte-Pair Encoding verwendet.
# Das Subwortlexikon wird zunächst auf basis der Wörter bzw. Sätze, die sich im
# Trainingskorpus befinden, gelernt und dann als Zielwörterbuch verwendet. Der Vorteil
# dieses Ansatzes ist, dass auch Wörter, die nicht im Lexikon verfügbar sind, auf Basis
# der Subworteinheiten erkannt werden können.

. ./cmd.sh
. ./path.sh

stage=0
num_jobs=24
num_decode_jobs=24
# Number of BPE merges
num_merges=1000
decode_gmm=true

. utils/parse_options.sh

set -euo pipefail

if [ $stage -le -1 ]; then
  mfccdir=mfcc
  for part in oed_test data/oed_train data/parl-br_cleaned data/parl-nr26_cleaned data/parl-nr27_cleaned data/wienbot_cleaned; do
    steps/make_mfcc.sh --cmd "$train_cmd" --nj $num_jobs data/$part exp/make_mfcc/$part $mfccdir
    steps/compute_cmvn_stats.sh data/$part exp/make_mfcc/$part $mfccdir
  done
fi

if [ $stage -le 0 ]; then
  utils/combine_data.sh data/train data/oed_train data/parl-br_cleaned data/parl-nr26_cleaned data/parl-nr27_cleaned data/wienbot_cleaned
  utils/copy_data_dir.sh data/oed_test data/test
fi

if [ $stage -le 1 ]; then
  echo "$0: Preparing lexicon and LM..." 
  local/prepare_dict_subword.sh --num_merges $num_merges

  utils/subword/prepare_lang_subword.sh data/local/dict "<unk>" data/local/lang data/lang

  for data in train test; do
    utils/subword/prepare_subword_text.sh data/${data}/text data/local/pair_code.txt data/${data}/text
  done

  local/prepare_lm_subword.sh

  utils/format_lm.sh data/lang data/local/lm/lm.gz \
    data/local/dict/lexicon.txt data/lang_test
fi

if [ $stage -le 2 ]; then
  # Get the shortest 500 utterances first because those are more likely
  # to have accurate alignments.
  utils/subset_data_dir.sh --shortest data/oed_train 10000 data/train.10K

  # train a monophone system
  steps/train_mono.sh --boost-silence 1.25 --nj $num_jobs --cmd "$train_cmd" \
    data/train.10K data/lang exp/mono_subword

  echo "$0: Aligning data using monophone system"
  steps/align_si.sh --boost-silence 1.25 --nj $num_jobs --cmd "$train_cmd" \
    data/train data/lang exp/mono_subword exp/mono_subword_ali_train
fi

# train a first delta + delta-delta triphone system on all utterances
if [ $stage -le 3 ]; then
  echo "$0: training triphone system with delta features"
  steps/train_deltas.sh --boost-silence 1.25 --cmd "$train_cmd" \
    2500 30000 data/train data/lang exp/mono_subword_ali_train exp/tri1_subword || exit 1;
fi

if [ $stage -le 4 ] && $decode_gmm; then
  utils/mkgraph.sh data/lang_test exp/tri1_subword exp/tri1_subword/graph
  steps/decode.sh  --nj $num_decode_jobs --cmd "$decode_cmd" \
    exp/tri1_subword/graph data/test exp/tri1_subword/decode
fi

# train an LDA+MLLT system.
if [ $stage -le 5 ]; then
  echo "$0: Aligning data and retraining and realigning with lda_mllt"
  steps/align_si.sh --nj $num_jobs --cmd "$train_cmd" \
    data/train data/lang exp/tri1_subword exp/tri1_ali_subword || exit 1;

  steps/train_lda_mllt.sh --cmd "$train_cmd" 4000 50000 \
    data/train data/lang exp/tri1_ali_subword exp/tri2b_subword || exit 1;
fi

if [ $stage -le 6 ] && $decode_gmm; then
  utils/mkgraph.sh data/lang_test exp/tri2b_subword exp/tri2b_subword/graph
  steps/decode.sh --nj $num_decode_jobs --cmd "$decode_cmd" \
    exp/tri2b_subword/graph data/test exp/tri2b_subword/decode
fi

if [ $stage -le 7 ]; then
  echo "$0: Aligning data and retraining and realigning with sat_basis"
  steps/align_si.sh --nj $num_jobs --cmd "$train_cmd" \
    data/train data/lang exp/tri2b_subword exp/tri2b_ali_subword || exit 1;

  steps/train_sat_basis.sh --cmd "$train_cmd" \
    5000 100000 data/train data/lang exp/tri2b_ali_subword exp/tri3b_subword || exit 1;

  steps/align_fmllr.sh --nj $num_jobs --cmd "$train_cmd" \
    data/train data/lang exp/tri3b_subword exp/tri3b_ali_subword || exit 1;
fi

if [ $stage -le 8 ] && $decode_gmm; then
  utils/mkgraph.sh data/lang_test exp/tri3b_subword exp/tri3b_subword/graph
  steps/decode_fmllr.sh --nj $num_decode_jobs --cmd \
    "$decode_cmd" exp/tri3b_subword/graph data/test exp/tri3b_subword/decode
fi

if [ $stage -le 9 ]; then
  echo "$0: Training a regular chain model using the e2e alignments..."
  local/chain2/run_tdnn.sh --gmm tri3b_subword --stage 22 --train-stage 533
fi
