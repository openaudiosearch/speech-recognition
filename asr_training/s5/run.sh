#!/usr/bin/env bash

. ./cmd.sh
. ./path.sh

stage=0
. utils/parse_options.sh

set -euo pipefail

if [ $stage -le 0 ]; then
  mkdir -p data/train
  awk '{id=$1; gsub(/\//, "-", id); gsub(/\.wav/, "", id); print id,$1}' /app/data/metadata.csv >data/train/wav.scp
  awk '{id=$1; gsub(/\//, "-", id); gsub(/\.wav/, "", id); gsub(/<unk> /, "", $2); print id,$2}' /app/data/metadata.csv >data/train/text
  awk '{id=$1; gsub(/\//, "-", id); gsub(/\.wav/, "", id); print id,id}' /app/data/metadata.csv >data/train/utt2spk
  utils/utt2spk_to_spk2utt.pl data/train/utt2spk >data/train/spk2utt
fi

if [ $stage -le 1 ]; then
  local/prepare_lm.sh
  local/prepare_dict.sh

  utils/prepare_lang.sh data/local/dict_nosp \
    "<unk>" data/local/lang_tmp_nosp data/lang_nosp

  utils/format_lm.sh data/lang_nosp data/local/lm.wb.3g.gz \
    data/local/dict_nosp/lexicon.txt data/lang_nosp_test

  # Create ConstArpaLm format language model for full 3-gram and 4-gram LMs
  # utils/build_const_arpa_lm.sh data/local/lm.wb.3g.gz data/lang_nosp \
    # data/lang_nosp_test_tglarge
fi

if [ $stage -le 2 ]; then
  mfccdir=mfcc
  for part in train; do
    steps/make_mfcc.sh --cmd "$train_cmd" --nj 10 data/$part exp/make_mfcc/$part $mfccdir
    steps/compute_cmvn_stats.sh data/$part exp/make_mfcc/$part $mfccdir
  done

  # Get the shortest 500 utterances first because those are more likely
  # to have accurate alignments.
  utils/subset_data_dir.sh --shortest data/train 500 data/train_500short
fi

# train a monophone system
if [ $stage -le 3 ]; then
  steps/train_mono.sh --boost-silence 1.25 --nj 5 --cmd "$train_cmd" \
    data/train_500short data/lang_nosp exp/mono

  steps/align_si.sh --boost-silence 1.25 --nj 5 --cmd "$train_cmd" \
    data/train data/lang_nosp exp/mono exp/mono_ali_train
fi

# train a first delta + delta-delta triphone system on all utterances
if [ $stage -le 4 ]; then
  steps/train_deltas.sh --boost-silence 1.25 --cmd "$train_cmd" \
    2000 10000 data/train data/lang_nosp exp/mono_ali_train exp/tri1

  steps/align_si.sh --nj 5 --cmd "$train_cmd" \
    data/train data/lang_nosp exp/tri1 exp/tri1_ali_train
fi

# train an LDA+MLLT system.
if [ $stage -le 5 ]; then
  steps/train_lda_mllt.sh --cmd "$train_cmd" \
    --splice-opts "--left-context=3 --right-context=3" 2500 15000 \
    data/train data/lang_nosp exp/tri1_ali_train exp/tri2b

  # Align utts using the tri2b model
  steps/align_si.sh  --nj 5 --cmd "$train_cmd" --use-graphs true \
    data/train data/lang_nosp exp/tri2b exp/tri2b_ali_train
fi

# Train tri3b, which is LDA+MLLT+SAT
if [ $stage -le 6 ]; then
  steps/train_sat.sh --cmd "$train_cmd" 2500 15000 \
    data/train data/lang_nosp exp/tri2b_ali_train exp/tri3b
fi

# Now we compute the pronunciation and silence probabilities from training data,
# and re-create the lang directory.
if [ $stage -le 7 ]; then
  steps/get_prons.sh --cmd "$train_cmd" \
    data/train data/lang_nosp exp/tri3b
  utils/dict_dir_add_pronprobs.sh --max-normalize true \
    data/local/dict_nosp \
    exp/tri3b/pron_counts_nowb.txt exp/tri3b/sil_counts_nowb.txt \
    exp/tri3b/pron_bigram_counts_nowb.txt data/local/dict

  utils/prepare_lang.sh data/local/dict \
    "<unk>" data/local/lang_tmp data/lang

  utils/format_lm.sh data/lang data/local/lm.wb.3g.gz data/local/dict/lexicon.txt data/lang_test

  utils/build_const_arpa_lm.sh data/local/lm.wb.3g.gz data/lang data/lang_test_tglarge

  steps/align_fmllr.sh --nj 5 --cmd "$train_cmd" \
    data/train data/lang exp/tri3b exp/tri3b_ali_train
fi


# if [ $stage -le 8 ]; then
#   # Test the tri3b system with the silprobs and pron-probs.

#   # decode using the tri3b model
#   utils/mkgraph.sh data/lang_test \
#                    exp/tri3b exp/tri3b/graph
#   for test_dataset in test; do
#     steps/decode_fmllr.sh --nj 10 --cmd "$decode_cmd" \
#                           exp/tri3b/graph data/${test_dataset} \
#                           exp/tri3b/decode_${test_dataset}
#     steps/lmrescore.sh --cmd "$decode_cmd" data/lang_test \
#                        data/$test exp/tri3b/decode_${test_dataset}
#     steps/lmrescore_const_arpa.sh \
#       --cmd "$decode_cmd" data/lang_test{,_tglarge} \
#       data/${test_dataset} exp/tri3b/decode{,_tglarge}_${test_dataset}
#   done
# fi

# Train a chain model
if [ $stage -le 9 ]; then
  local/chain2/tuning/run_tdnn_1a.sh
fi
