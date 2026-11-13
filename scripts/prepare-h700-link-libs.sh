#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS adaptation by D4n1984.
# Link-only EGL/GLES libraries with standard SONAMEs. Never ship these with muOS.
# Knulli's SDK shims export no GL entry points and otherwise require libmali.so.0.
set -euo pipefail
dest_dir="${1:?Usage: prepare-h700-link-libs.sh destination}"
mkdir -p "$dest_dir"
cd "$dest_dir"
cat > packages.sha256 <<'HASHES'
13227c1e594d4e6457831f3ef4eb2dff2614dc65e4622f69f2de0105d0acce54  libegl1_1.4.0-1_arm64.deb
9bf9ad9dbaa08ffb84bd3af8f128b218590820d939f49bd5ab8de7e242c99677  libgles2_1.4.0-1_arm64.deb
47e4a53b0b3bbf007e2e4e7efb481ec4db4d127914b0d355550092549911a99d  libglvnd0_1.4.0-1_arm64.deb
HASHES
for package in libegl1 libgles2 libglvnd0; do
    archive="${package}_1.4.0-1_arm64.deb"
    if [ ! -f "$archive" ]; then
        curl -fL --retry 3 "https://ports.ubuntu.com/pool/main/libg/libglvnd/$archive" \
            -o "$archive"
    fi
done
sha256sum --check packages.sha256
for package in libegl1 libgles2 libglvnd0; do
    dpkg-deb -x "${package}_1.4.0-1_arm64.deb" root
done
