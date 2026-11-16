FROM --platform=linux/amd64 ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential g++-multilib libc6-i386 lib32stdc++6 lib32z1 \
    make python3 ca-certificates file binutils libssl-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
# Supply your licensed full ARM-target QNX SDP 6.5 installation as /opt/qnx650.
# This image contains no proprietary SDK, license, activation bypass, or vehicle files.
ENV QNX_HOST=/opt/qnx650/host/linux/x86 QNX_TARGET=/opt/qnx650/target/qnx6
ENV PATH=/opt/qnx650/host/linux/x86/usr/bin:$PATH
