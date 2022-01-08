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

# Number of parallel feature extraction jobs
ARG NJ_FEAT=10
ENV NJ_FEAT=$NJ_FEAT

# Number of parallel training jobs
ARG NJ_TRAIN=10
ENV NJ_TRAIN=$NJ_TRAIN

# Number of parallel decode jobs
ARG NJ_DECODE=10
ENV NJ_DECODE=$NJ_DECODE

# Whether to decode after each training step
ARG DO_DECODE=1
ENV DO_DECODE=$DO_DECODE

# Number of parallel training jobs
ARG STAGE=0
ENV STAGE=$STAGE

COPY s5 /opt/kaldi/egs/oas/s5
COPY s5_subword /opt/kaldi/egs/oas/s5_subword

WORKDIR /opt/kaldi/egs/oas/s5

ENTRYPOINT ["/bin/bash", "run.sh"]
# ENTRYPOINT ["run.sh"]
