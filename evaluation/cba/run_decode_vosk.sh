#!/bin/bash

set -e

stage=$STAGE
test_set="cba_testdaten_kaldi"
asr_nnet_dir=exp/vosk-model-de-0.21

ln -s ../../wsj/s5/steps
ln -s ../../wsj/s5/utils
export KALDI_ROOT=`pwd`/../../..
[ -f $KALDI_ROOT/tools/env.sh ] && . $KALDI_ROOT/tools/env.sh
export PATH=$PWD/utils/:$KALDI_ROOT/tools/openfst/bin:$PWD:$PATH
[ ! -f $KALDI_ROOT/tools/config/common_path.sh ] && echo >&2 "The standard file $KALDI_ROOT/tools/config/common_path.sh is not present -> Exit!" && exit 1
. $KALDI_ROOT/tools/config/common_path.sh

# Download Vosk ASR model
if [ ! -d "$asr_nnet_dir" ]; then
  wget -O /tmp/vosk-model-de-0.21.zip https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip
  unzip -d exp/ /tmp/vosk-model-de-0.21.zip
  rm /tmp/vosk-model-de-0.21.zip
fi

# Create i-vector extraction config missing from Vosk model distribution
# (Vosk hard-codes these values in its C code.)
cat >$asr_nnet_dir/conf/ivector_extractor.conf <<EOF
--cmvn-config=/opt/kaldi/egs/oas/s5/$asr_nnet_dir/ivector/online_cmvn.conf
--ivector-period=10
--splice-config=/opt/kaldi/egs/oas/s5/$asr_nnet_dir/ivector/splice.conf
--lda-matrix=/opt/kaldi/egs/oas/s5/$asr_nnet_dir/ivector/final.mat
--global-cmvn-stats=/opt/kaldi/egs/oas/s5/$asr_nnet_dir/ivector/global_cmvn.stats
--diag-ubm=/opt/kaldi/egs/oas/s5/$asr_nnet_dir/ivector/final.dubm
--ivector-extractor=/opt/kaldi/egs/oas/s5/$asr_nnet_dir/ivector/final.ie
--num-gselect=5
--min-post=0.025
--posterior-scale=0.1
--max-remembered-frames=1000
--max-count=100
EOF

if [ ! -d "/data/cba_test_200408" ]; then
  # Download CBA test audio data
  ~/.local/bin/gdown -O /tmp/cba_test_200408.tar.gz https://drive.google.com/uc?id=1RX83596ZzMxjDhzcvoakO33HqB6zTAA8
  mkdir -p /data
  cd /data/
  tar xvf /tmp/cba_test_200408.tar.gz
  cd /opt/kaldi/egs/oas/s5
fi

# Perform speech recognition
if [ $stage -le 0 ]; then
  dir=$asr_nnet_dir/decode_${test_set}
  mkdir -p $dir
  lat_wspecifier="ark:|/opt/kaldi/src/latbin/lattice-scale --acoustic-scale=10.0 ark:- ark:- | gzip -c >$dir/lat.1.gz"
  /opt/kaldi/src/online2bin/online2-wav-nnet3-latgen-faster --do-endpointing=false \
    --frames-per-chunk=20 \
    --mfcc-config=$asr_nnet_dir/conf/mfcc.conf \
    --ivector-extraction-config=$asr_nnet_dir/conf/ivector_extractor.conf \
    --extra-left-context-initial=0 \
    --online=true \
    --config=$asr_nnet_dir/conf/model.conf \
    --word-symbol-table=$asr_nnet_dir/graph/words.txt \
    $asr_nnet_dir/am/final.mdl $asr_nnet_dir/graph/HCLG.fst ark:data/${test_set}/spk2utt \
    "ark,s,cs:/opt/kaldi/src/featbin/extract-segments scp,p:data/${test_set}/wav.scp data/${test_set}/segments ark:- |" \
    "$lat_wspecifier" || exit 1;
fi

# Perform scoring
if [ $stage -le 1 ]; then
  steps/score_kaldi.sh data/${test_set} $asr_nnet_dir/graph $asr_nnet_dir/decode_${test_set}
  cat $asr_nnet_dir/decode_${test_set}/scoring_kaldi/best_wer
fi

# N-gram LM rescoring
if [ $stage -le 2 ]; then
  indir=$asr_nnet_dir/decode_${test_set}
  outdir=$asr_nnet_dir/decode_${test_set}_rescore
  mkdir -p $outdir
  /opt/kaldi/src/latbin/lattice-lmrescore --lm-scale=-1.0 \
    "ark:gunzip -c $indir/lat.1.gz|" \
    "/opt/kaldi/tools/openfst/bin/fstproject --project_output=true $asr_nnet_dir/rescore/G.fst |" ark:- | \
    /opt/kaldi/src/latbin/lattice-lmrescore-const-arpa --lm-scale=1.0 \
    ark:- "$asr_nnet_dir/rescore/G.carpa" "ark,t:|gzip -c>$outdir/lat.1.gz" || exit 1;
fi

# Perform scoring
if [ $stage -le 3 ]; then
  steps/score_kaldi.sh data/${test_set} $asr_nnet_dir/graph $asr_nnet_dir/decode_${test_set}_rescore
  cat $asr_nnet_dir/decode_${test_set}_rescore/scoring_kaldi/best_wer
fi
exit 0
