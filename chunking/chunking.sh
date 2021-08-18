#!/usr/bin/env bash

. ./cmd.sh
. ./path.sh

stage=0
# Data directories (located in data/) that should be chunked
data_dirs=parl-br parl-nr26 parl-nr27


. utils/parse_options.sh

set -euo pipefail

# Feature extraction
if [ $stage -le 0 ]; then
  mfccdir=mfcc
  for part in $data_dirs; do
    steps/make_mfcc.sh --cmd "$train_cmd" --nj 12 data/$part exp/make_mfcc/$part $mfccdir
    steps/compute_cmvn_stats.sh data/$part exp/make_mfcc/$part $mfccdir
  done
fi

# Chunking (segmentation) step
if [ $stage -le 1 ]; then
  for part in $data_dirs; do
    steps/cleanup/segment_long_utterances.sh --cmd "$train_cmd" --nj 24 \
      exp/tri3b data/lang_nosp data/${part} data/${part}_reseg exp/segment_${part}
    utils/fix_data_dir.sh data/${part}_reseg
  done
fi

# Feature extraction of chunked/segmented data
if [ $stage -le 2 ]; then
  mfccdir=mfcc
  for part in $data_dirs; do
    steps/make_mfcc.sh --cmd "$train_cmd" --nj 24 data/${part}_reseg exp/make_mfcc/${part}_reseg $mfccdir
    steps/compute_cmvn_stats.sh data/${part}_reseg exp/make_mfcc/${part}_reseg $mfccdir
  done
fi

# Alignment step of chunked/segmented data
if [ $stage -le 3 ]; then
  for part in $data_dirs; do
    steps/align_fmllr.sh --nj 24 --cmd "$train_cmd" \
      data/${part}_reseg data/lang_nosp exp/tri3b exp/tri3b_ali_${part}_reseg
  done
fi

# Additional cleaning step of the already chunked material
if [ $stage -le 4 ]; then
  for part in $data_dirs; do
    steps/cleanup/clean_and_segment_data.sh --cmd "$train_cmd" --nj 24 \
      data/${part}_reseg data/lang_nosp exp/tri3b_ali_${part}_reseg exp/tri3b_${part}_cleanup data/${part}_cleaned
  done
fi

# Print duration in hours after chunking and cleanup
for part in $data_dirs; do
  awk '{x += $4 - $3;} END{print x/3600;}' <data/${part}_reseg/segments
done
