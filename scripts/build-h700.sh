#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS adaptation by D4n1984.
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${BUILD_DIR:-$repo_dir/build-h700}"
: "${H700_SDK:?Set H700_SDK to the relocated Knulli H700 SDK directory}"
export H700_SDK
bash "$repo_dir/scripts/prepare-h700-link-libs.sh" "$build_dir/link-libs"
link_lib_dir="$build_dir/link-libs/root/usr/lib/aarch64-linux-gnu"
cmake -S "$repo_dir/yabause" -B "$build_dir" \
    -DCMAKE_TOOLCHAIN_FILE="$repo_dir/cmake/toolchains/h700-linux.cmake" \
    -DCMAKE_BUILD_TYPE=Release \
    -DYAB_TARGET_H700=ON -DYAB_PORTS=retro_arena \
    -DYAB_WANT_DYNAREC_DEVMIYAX=ON -DYAB_WANT_VULKAN=OFF \
    -DYAB_WANT_OPENAL=OFF -DUSE_EGL=ON \
    -DCMAKE_DISABLE_FIND_PACKAGE_X11=ON \
    -DCMAKE_DISABLE_FIND_PACKAGE_GLUT=ON \
    -DYAB_EGL_LIBRARY="$link_lib_dir/libEGL.so.1" \
    -DYAB_GLES_LIBRARY="$link_lib_dir/libGLESv2.so.2" \
    -DOPENGLES_gl2_LIBRARY="$link_lib_dir/libGLESv2.so.2" \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,-rpath-link,$link_lib_dir" \
    -DCMAKE_SKIP_RPATH=ON \
    "$@"
cmake --build "$build_dir" --parallel "${JOBS:-4}"
mkdir -p "$build_dir/output"
"$H700_SDK/bin/aarch64-buildroot-linux-gnu-strip" \
    -o "$build_dir/output/yabasanshiro-h700" \
    "$build_dir/src/retro_arena/yabasanshiro"
cp -R "$repo_dir/packaging/muos-h700/." "$build_dir/output/"
chmod +x "$build_dir/output/"*.sh "$build_dir/output/yabasanshiro-h700"
cp "$repo_dir/LICENSE" "$repo_dir/THIRD-PARTY-NOTICES.md" "$build_dir/output/"
(cd "$build_dir/output" && sha256sum yabasanshiro-h700 > SHA256SUMS)
printf 'Build complete: %s/output\n' "$build_dir"
