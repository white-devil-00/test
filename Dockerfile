FROM alpine:edge

ARG TARGETPLATFORM BUILDPLATFORM

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

# Installing basic packages
RUN apk update && apk upgrade && \
    apk add --upgrade --no-cache \
    sudo py3-wheel musl-dev musl python3 \
    python3-dev busybox musl-locales github-cli lshw \
    qbittorrent-nox py3-pip py3-lxml aria2 p7zip \
    xz curl pv jq ffmpeg parallel \
    neofetch git make g++ gcc automake zip unzip \
    autoconf speedtest-cli bash \
    musl-utils tzdata gcompat libmagic \
    libffi-dev py3-virtualenv libffi \
    dpkg cmake icu-data-full apk-tools \
    coreutils npm bash-completion bash-doc && \
    sed -i -e "s/bin\/ash/bin\/bash/" /etc/passwd

SHELL ["/bin/bash", "-c"]

# Installing Build Tools
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories && \
    sudo apk add --upgrade --no-cache \
    libtool curl-dev libsodium-dev c-ares-dev sqlite-dev freeimage-dev swig boost-dev \
    libpthread-stubs zlib zlib-dev libpq-dev clang clang-dev ccache gettext gettext-dev \
    gawk crypto++ crypto++-dev libjpeg-turbo-dev 

# Building and Installing MegaSdkC++
ENV PYTHONWARNINGS=ignore
ENV MEGA_SDK_VERSION="4.10.0"
RUN git clone https://github.com/meganz/sdk.git -b v$MEGA_SDK_VERSION  ~/home/sdk && \
    cd ~/home/sdk && rm -rf .git && \
    autoupdate -fIv && ./autogen.sh && \
    ./configure CFLAGS='-fpermissive' CXXFLAGS='-fpermissive' CPPFLAGS='-fpermissive' CCFLAGS='-fpermissive' \
    --disable-silent-rules --enable-python --with-sodium --disable-examples --with-python3 && \
    make -j$(nproc --all) && \
    cd bindings/python/ && \
    python3 setup.py bdist_wheel && \
    cd dist && ls && \
    pip3 install *.whl

# Install Rclone
RUN curl https://rclone.org/install.sh | bash 

# Installing Bot Requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Setup Language Environments
ENV LANG="en_US.UTF-8" LANGUAGE="en_US:en" LC_ALL="en_US.UTF-8"
RUN echo 'export LC_ALL=en_US.UTF-8' >> /etc/profile.d/locale.sh && \
    sed -i 's|LANG=C.UTF-8|LANG=en_US.UTF-8|' /etc/profile.d/locale.sh && \
    rm -rf *

# Running Final Apk Update
RUN sudo apk update && apk upgrade

COPY . .

CMD ["bash", "start.sh"]
