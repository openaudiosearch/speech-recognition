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

RUN cd /opt/kaldi/tools && \
    ./extras/install_kaldi_lm.sh && \
    ./extras/install_phonetisaurus.sh

FROM nvidia/cuda:11.3.0-runtime-ubuntu20.04

COPY --from=build /opt/kaldi /opt/kaldi

# These two lines prevent problems with using Ubuntu's apt-get non-interactively
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Vienna

RUN apt-get update && apt-get install -y --no-install-recommends \
        locales sox python2.7 python3 python-is-python3 ffmpeg \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN locale-gen de_DE.UTF-8
ENV LC_ALL=de_DE.UTF-8
ENV LANG=de_DE.UTF-8

COPY s5 /opt/kaldi/egs/oas/s5
COPY s5_subword /opt/kaldi/egs/oas/s5_subword

WORKDIR /opt/kaldi/egs/oas/s5

ENTRYPOINT ["/bin/bash", "run.sh"]
# ENTRYPOINT ["run.sh"]
