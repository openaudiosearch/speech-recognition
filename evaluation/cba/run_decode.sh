#!/bin/bash

. ./cmd.sh
. ./path.sh
set -e

stage=0
test_sets="cba_testdaten_kaldi"
asr_nnet_dir=$ASR_NNET_DIR
nnet3_affix=
tree_affix=
chunk_width=140,100,160
gmm=tri3b
nj=1

# Problem: We have removed the "train_" prefix of our training set in
# the alignment directory names! Bad!
gmm_dir=exp/$gmm
ali_dir=exp/${gmm}_ali_${train_set}_sp
tree_dir=exp/chain2${nnet3_affix}/tree_sp${tree_affix:+_$tree_affix}
lang=data/lang_chain
lat_dir=exp/chain2${nnet3_affix}/${gmm}_${train_set}_sp_lats
dir=exp/chain2${nnet3_affix}/tdnn${affix}_sp
train_data_dir=data/${train_set}_sp_hires
lores_train_data_dir=data/${train_set}_sp
train_ivector_dir=exp/nnet3${nnet3_affix}/ivectors_${train_set}_sp_hires

model_left_context=$(awk '/^model_left_context/ {print $2;}' $asr_nnet_dir/init/info.txt)
model_right_context=$(awk '/^model_right_context/ {print $2;}' $asr_nnet_dir/init/info.txt)
if [ -z $model_left_context ]; then
    echo "ERROR: Cannot find entry for model_left_context in $asr_nnet_dir/init/info.txt"
fi
if [ -z $model_right_context ]; then
    echo "ERROR: Cannot find entry for model_right_context in $asr_nnet_dir/init/info.txt"
fi
# Note: we add frame_subsampling_factor/2 so that we can support the frame
# shifting that's done during training, so if frame-subsampling-factor=3, we
# train on the same egs with the input shifted by -1,0,1 frames.  This is done
# via the --frame-shift option to nnet3-chain-copy-egs in the script.
egs_left_context=$[model_left_context+(frame_subsampling_factor/2)+egs_extra_left_context]
egs_right_context=$[model_right_context+(frame_subsampling_factor/2)+egs_extra_right_context]


if [ $stage -le -1 ]; then
  for datadir in ${test_sets}; do
    utils/copy_data_dir.sh data/$datadir data/${datadir}_hires
    steps/make_mfcc.sh --nj $nj --mfcc-config conf/mfcc_hires.conf \
      --cmd "$train_cmd" data/${datadir}_hires || exit 1;
    steps/compute_cmvn_stats.sh data/${datadir}_hires || exit 1;
    utils/fix_data_dir.sh data/${datadir}_hires || exit 1;
    # Also extract iVectors for the test data, but in this case we don't need the speed
    # perturbation (sp).
    steps/online/nnet2/extract_ivectors_online.sh --cmd "$train_cmd" --nj $nj \
      data/${datadir}_hires exp/nnet3${nnet3_affix}/extractor \
      exp/nnet3${nnet3_affix}/ivectors_${datadir}_hires
  done
fi

# Perform speech recognition
if [ $stage -le 0 ]; then
  frames_per_chunk=$(echo $chunk_width | cut -d, -f1)
  # Do the speaker-dependent decoding pass
  for data in $test_sets; do
    (
      nspk=$(wc -l <data/${data}_hires/spk2utt)
      steps/nnet3/decode.sh \
          --acwt 1.0 --post-decode-acwt 10.0 \
          --extra-left-context $egs_left_context \
          --extra-right-context $egs_right_context \
          --extra-left-context-initial 0 \
          --extra-right-context-final 0 \
          --frames-per-chunk $frames_per_chunk \
          --nj $nj --cmd "$decode_cmd"  --num-threads 4 \
          --online-ivector-dir exp/nnet3${nnet3_affix}/ivectors_${data}_hires \
          $tree_dir/graph data/${data}_hires ${asr_nnet_dir}/decode_${data} || exit 1
      #steps/lmrescore_const_arpa.sh --cmd "$decode_cmd" \
      #  data/lang_test{,_tglarge} \
      # data/${data}_hires ${asr_nnet_dir}/decode{,_tglarge}_${data} || exit 1
    ) || touch $asr_nnet_dir/.error
  done
  #wait
  [ -f $asr_nnet_dir/.error ] && echo "$0: there was a problem while decoding" && exit 1
fi

# Perform scoring
if [ $stage -le 2 ]; then
  local/score.sh --cmd "$train_cmd" $scoring_opts data/${test_sets} $asr_nnet_dir/graph $asr_nnet_dir/decode_${test_sets}
fi

# Get automatic transcripts in Conversation Time Mark (CTM) format
if [ $stage -le 3 ]; then
  mkdir -p exp/ctm_${name}
  local/get_ctm.sh --frame-shift 0.03 data/${name}_seg $asr_nnet_dir/data/lang $asr_nnet_dir/decode_${name}
fi

# Reformat CTM files and split them according to recording IDs
if [ $stage -le 4 ]; then
  mkdir -p exp/ctm_${name}
  awk '{print $2}' data/${name}_seg/segments | sort -u |\
  while read rec; do
    grep "$rec" $asr_nnet_dir/decode_${name}/score_10/${name}_seg.ctm | tr "-" "_" >exp/ctm_${name}/$rec.ctm
  done
fi
