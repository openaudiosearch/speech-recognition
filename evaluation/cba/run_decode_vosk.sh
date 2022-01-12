#!/bin/bash

. ./cmd.sh
. ./path.sh
set -e

stage=$STAGE
test_set="cba_testdaten_kaldi"
asr_nnet_dir=exp/vosk-model-de-0.21

# Download Vosk ASR model
if [ ! -d "$asr_nnet_dir" ]; then
  wget -O /tmp/vosk-model-de-0.21.zip https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip
  unzip -q -d exp/ /tmp/vosk-model-de-0.21.zip
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
  # Install gdown if it isn't available
  if [ ! command -v gdown &>/dev/null ]; then
    pip install --user gdown
  fi
  # Download CBA test audio data
  gdown https://drive.google.com/uc?id=1RX83596ZzMxjDhzcvoakO33HqB6zTAA8
fi

# Perform speech recognition
if [ $stage -le 0 ]; then
  dir=$asr_nnet_dir/decode_${test_set}
  mkdir -p $dir
  lat_wspecifier="ark:|/opt/kaldi/src/latbin/lattice-scale --acoustic-scale=10.0 ark:- ark:- | gzip -c >$dir/lat.JOB.gz"
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

  # steps/lmrescore_const_arpa.sh --cmd "$decode_cmd" \
      #  data/lang_test{,_tglarge} \
      # data/${data}_hires ${asr_nnet_dir}/decode{,_tglarge}_${data} || exit 1
    # ) || touch $asr_nnet_dir/.error
fi

# N-gram LM rescoring
if [ $stage -le 1 ]; then
  indir=$asr_nnet_dir/decode_${test_set}
  outdir=$asr_nnet_dir/decode_${test_set}_rescore
  /opt/kaldi/src/latbin/lattice-lmrescore --lm-scale=-1.0 \
    "ark:gunzip -c $indir/lat.JOB.gz|" \
    "/opt/kaldi/tools/openfst/bin/fstproject --project_output=true $asr_nnet_dir/rescore/G.fst |" ark:- \| \
    /opt/kaldi/src/latbin/lattice-lmrescore-const-arpa --lm-scale=1.0 \
    ark:- "$asr_nnet_dir/rescore/G.carpa" "ark,t:|gzip -c>$outdir/lat.JOB.gz" || exit 1;
fi

# Perform scoring
if [ $stage -le 2 ]; then
  local/score.sh --cmd "$train_cmd" $scoring_opts data/${test_set} $asr_nnet_dir/graph $asr_nnet_dir/decode_${test_set}
fi
exit 0
# Get automatic transcripts in Conversation Time Mark (CTM) format
if [ $stage -le 3 ]; then
  mkdir -p exp/ctm_${test_set}
  local/get_ctm.sh --frame-shift 0.03 data/${test_set}_seg $asr_nnet_dir/data/lang $asr_nnet_dir/decode_${test_set}
fi

# Reformat CTM files and split them according to recording IDs
if [ $stage -le 4 ]; then
  mkdir -p exp/ctm_${test_set}
  awk '{print $2}' data/${test_set}_seg/segments | sort -u |\
  while read rec; do
    grep "$rec" $asr_nnet_dir/decode_${test_set}/score_10/${test_set}_seg.ctm | tr "-" "_" >exp/ctm_${test_set}/$rec.ctm
  done
fi
