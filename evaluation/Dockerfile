# FROM pykaldi/pykaldi:latest
#FROM nvidia/cuda:10.0-cudnn7-devel-ubuntu18.04
FROM nvidia/cuda:11.3.0-devel-ubuntu20.04 as build

# These two lines prevent problems with using Ubuntu's apt-get non-interactively
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Vienna

RUN apt-get update && apt-get install -y --no-install-recommends \
        g++ \
        make \
        automake \
        autoconf \
        bzip2 \
        unzip \
        wget \
        sox \
        libtool \
        git \
        subversion \
        python2.7 \
        python3 \
        python-is-python3 \
        zlib1g-dev \
        gfortran \
        ca-certificates \
        patch \
        liblbfgs-dev \
        gawk \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/kaldi-asr/kaldi.git /opt/kaldi && \
    cd /opt/kaldi/tools && \
    ./extras/install_openblas.sh && \
    make -j $(nproc) && \
    cd /opt/kaldi/src && \
    ./configure --shared --use-cuda --mathlib=OPENBLAS --debug-level=0 && \
    make depend -j $(nproc) && \
    make -j $(nproc) && \
    find /opt/kaldi  -type f \( -name "*.o" -o -name "*.la" -o -name "*.a" \) -exec rm {} \; && \
    rm -rf /opt/kaldi/.git
    #find /opt/intel -type f -name "*.a" -exec rm {} \; && \
    #find /opt/intel -type f -regex '.*\(_mc.?\|_mic\|_thread\|_ilp64\)\.so' -exec rm {} \; && \

RUN mkdir -p /opt/kaldi/tools/liblbfgs-1.10

RUN cd /opt/kaldi/tools && \
    ./extras/install_srilm.sh OAS openaudiosearch info@arso.xyz


FROM nvidia/cuda:11.3.0-runtime-ubuntu20.04

COPY --from=build /opt/kaldi /opt/kaldi

# These two lines prevent problems with using Ubuntu's apt-get non-interactively
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Vienna

RUN apt-get update && apt-get install -y --no-install-recommends \
        locales sox python2.7 python3 python-is-python3 libgfortran5 libencode-perl liblbfgs0 \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen de_DE.UTF-8
ENV LC_ALL=de_DE.UTF-8
ENV LANG=de_DE.UTF-8

# Processing stage
ARG STAGE=0
ENV STAGE=$STAGE

# Number of parallel training jobs
ARG ASR_NNET_DIR=exp/vosk-model-de-0.21
ENV ASR_NNET_DIR=$ASR_NNET_DIR

COPY cba/cba_testdaten_kaldi /opt/kaldi/egs/oas/s5/data/cba_testdaten_kaldi
COPY cba/run_decode.sh /opt/kaldi/egs/oas/s5/run_decode.sh
COPY cba/run_decode_vosk.sh /opt/kaldi/egs/oas/s5/run_decode_vosk.sh

WORKDIR /opt/kaldi/egs/oas/s5

ENTRYPOINT ["/bin/bash", "run_decode_vosk.sh"]
