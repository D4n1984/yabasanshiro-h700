# YabaSanshiro H700

This is [@D4n1984](https://github.com/D4n1984)'s H700 adaptation of [Pirry's fork](https://github.com/pirrypirrypirry/yabasanshiro-pirry), targeting RG34XXSP with muOS. It is a standalone AArch64 Sega Saturn emulator using the SH-2 dynarec and EGL/OpenGL ES 3. Find the source in [this fork](https://github.com/D4n1984/yabasanshiro-h700); its [releases page](https://github.com/D4n1984/yabasanshiro-h700/releases) is the destination for future builds.

The repository does not contain binaries, BIOS files, ROMs or save states. See the [muOS package guide](packaging/muos-h700/README.md) for installation and limitations.

## Credits and contributions

- The [Yabause team](https://yabause.org/) created Yabause, the emulator core.
- [devMiyax](https://github.com/devmiyax/yabause) develops Yaba Sanshiro; this tree builds on its `pi4` branch and `retro_arena` port.
- [Pirry](https://github.com/pirrypirrypirry/yabasanshiro-pirry) contributed the R36S fork, including dynarec and rendering optimizations, audio and game fixes, the extended menu and multi-disc support.
- D4n1984 adapted the fork for H700: Cortex-A53 cross-compilation with GCC 12.3, GLES 3 and runtime SONAME configuration, SDL controller mapping fallback, more robust M3U handling, muOS integration, optional LTO, and capture and performance-sampling scripts.

Thanks to all upstream authors and contributors.

Clone the fork and initialize its Eigen submodule before building:

```bash
git clone --recursive https://github.com/D4n1984/yabasanshiro-h700.git
cd yabasanshiro-h700
```

For an existing clone, run `git submodule update --init --recursive`.

## Building for Allwinner H700 (RG34XXSP / muOS)

The H700 target uses AArch64 Cortex-A53 code, the SH-2 dynarec, SDL2 audio
and EGL/OpenGL ES 3. Cross-compilation uses the Knulli GCC 12.3 SDK from Linux or WSL.
Install host `build-essential`, `cmake`, `git`, `pkg-config`, `python3`,
`curl` and `dpkg-dev`.
Fetch and relocate the [Knulli H700 SDK (20240421)](https://github.com/knulli-cfw/toolchains/releases/tag/rg35xx-plush-sdk-20240421):

```bash
curl -fL --retry 3 -O https://github.com/knulli-cfw/toolchains/releases/download/rg35xx-plush-sdk-20240421/aarch64-buildroot-linux-gnu_sdk-buildroot.tar.gz
tar -xzf aarch64-buildroot-linux-gnu_sdk-buildroot.tar.gz
export H700_SDK="$PWD/aarch64-buildroot-linux-gnu_sdk-buildroot"
(cd "$H700_SDK" && ./relocate-sdk.sh)
# From this repository (including its Eigen submodule):
bash scripts/build-h700.sh
```

`BUILD_DIR` selects the build directory and `JOBS` the parallel job count
(default 4). Output is in `build-h700/output`, including the binary, launcher,
licenses and checksum. Read `packaging/muos-h700/README.md` for installation.
The build script downloads hash-checked Ubuntu ARM64 GLVND libraries for
linking against standard EGL/GLES SONAMEs instead of Knulli's Mali shims.
These link-only libraries are not included in the runtime package.
Use muOS's own SDL2/EGL/GLES libraries at runtime. The SDK is from Knulli;
the package has been checked on RG34XXSP with muOS 2606.0.
Compatibility and performance across games and firmware versions require further testing.

For a separate experimental LTO build, keep the validated build directory and use:

```bash
BUILD_DIR="$PWD/build-h700-lto" bash scripts/build-h700.sh -DYAB_ENABLE_LTO=ON
```

The default remains LTO off. CMake checks compiler support before enabling it
for the emulator targets; the bundled external dependency builds are separate.

### Recording comparison videos over SSH

`scripts/record-muos-screen.py` captures the active 720x480 framebuffer and
encodes MP4 on the host PC. It requires host `ffmpeg` and Python `paramiko`,
device Python 3, and the device's SSH host key already in `known_hosts`.
Set `MUOS_HOST` to your device's IP address, then run:

```bash
python3 scripts/record-muos-screen.py --host "$MUOS_HOST" \
  --seconds 20 --fps 15 --output build-h700/recordings/baseline.mp4
```

The password is requested interactively. `--known-hosts` selects another
host-key file when needed, for example when using WSL with Windows SSH files.
Capture has no audio and writes an accompanying JSON with actual frame times
and capture rate. Video timing follows the device timestamps; when capture
falls behind, the preceding image is repeated rather than speeding up the
footage. Reduce `--fps` if needed (10 fps worked reliably during the H700 test).
Keep the display mode fixed during each recording. These
videos compare rendered images, not 60 fps smoothness: measure performance in
separate runs without capture. `scripts/sample-muos-performance.py` collects
CPU time, emulated frame counts and available thermal/frequency sensors from
an already running process; it needs that exact executable's counter address.
Optional repeated `--gauge NAME=ADDRESS` arguments record uint32 instantaneous
values, such as the FPS overlay's last completed window. These addresses must
also come from the exact running executable. Restore the same saved scene
before each run and verify the scene visually; a successful state-load return
code alone does not establish a valid comparison.


## Legacy RK3326 / RK3566 build instructions

These instructions are inherited from Pirry's R36S project and describe that target.

Pirry built the emulator as a native **aarch64 Linux** program. The release
binaries are built on **Debian 13 (trixie), arm64** with GCC 14 and CMake 3.31.
The resulting binary needs **glibc 2.38 or newer** on the handheld (dArkOS).

### 1. Install the build dependencies

```bash
sudo apt install build-essential cmake git pkg-config \
    libsdl2-dev libgles-dev libegl-dev libgbm-dev libdrm-dev libudev-dev \
    libasound2-dev libopenal-dev libpng-dev zlib1g-dev
```

### 2. Get the source

```bash
git clone --recursive https://github.com/pirrypirrypirry/yabasanshiro-pirry.git
cd yabasanshiro-pirry
```

`--recursive` is required — it fetches the Eigen submodule used by the menu.
If you already cloned without it: `git submodule update --init --recursive`.

During the build CMake also downloads `libchdr`, `zlib` and `nlohmann/json`
from GitHub and `libpng` from SourceForge, so the build machine needs internet
access.

### 3. Configure

```bash
mkdir build && cd build
cmake ../yabause \
  -DCMAKE_BUILD_TYPE=Release \
  -DYAB_PORTS=retro_arena \
  -DYAB_WANT_DYNAREC_DEVMIYAX=ON \
  -DYAB_WANT_VULKAN=OFF \
  -DUSE_EGL=ON \
  -DCMAKE_C_FLAGS="-O3 -mcpu=cortex-a35 -fno-strict-aliasing -D_GNU_SOURCE -Wno-implicit-function-declaration -Wno-incompatible-pointer-types -Wno-int-conversion" \
  -DCMAKE_CXX_FLAGS="-O3 -mcpu=cortex-a35 -fno-strict-aliasing -D_GNU_SOURCE" \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,--allow-multiple-definition"
```

Every option matters:

| Option | Why |
|---|---|
| `-DUSE_EGL=ON` | Without it the shaders are built for desktop OpenGL and the emulator fails with *"Cannot initialize shader"* on the handheld |
| `-DYAB_WANT_DYNAREC_DEVMIYAX=ON` | The SH-2 dynarec — most of the speed comes from it |
| `-mcpu=cortex-a35` | Tunes the code for the RK3326 |
| `-Wno-…` flags | Parts of the old C code don't build with GCC 14 otherwise |
| `--allow-multiple-definition` | `nvgCreateGLES3` is defined twice in the bundled nanovg/nanogui code |

### 4. Build

```bash
make -j$(nproc)
strip -o yabasanshiro-pirry src/retro_arena/yabasanshiro
```

The finished emulator is `build/yabasanshiro-pirry`. Install it as
described on the [release page](https://github.com/pirrypirrypirry/yabasanshiro-pirry-release#installation).

### Optional: build exactly like the release (LTO)

The release binary additionally uses link-time optimization. Add `-flto=4 -fno-fat-lto-objects`
to both `CMAKE_C_FLAGS` and `CMAKE_CXX_FLAGS`, and pass:

```bash
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,--allow-multiple-definition -flto=4 -O3 -mcpu=cortex-a35" \
  -DCMAKE_AR=/usr/bin/gcc-ar -DCMAKE_RANLIB=/usr/bin/gcc-ranlib
```

### Building on an x86 PC (arm64 chroot)

No arm64 machine at hand? An arm64 Debian chroot with QEMU user emulation
works fine — it is how Pirry built the R36S releases. Expect a full build to take
around 15 minutes.

```bash
sudo apt install debootstrap qemu-user-static binfmt-support
sudo debootstrap --arch=arm64 trixie /srv/trixie-arm64 http://deb.debian.org/debian
sudo cp /etc/resolv.conf /srv/trixie-arm64/etc/
sudo chroot /srv/trixie-arm64 /bin/bash
# inside the chroot: steps 1–4 above
```

 ### Building for RK3566 (Cortex-A55)

  Pirry developed and tested the original project on RK3326 (Cortex-A35). An RK3326 build
  also runs on RK3566 handhelds. To tune the build for that chip instead, replace
  `-mcpu=cortex-a35` with `-mcpu=cortex-a55` in `CMAKE_C_FLAGS` and `CMAKE_CXX_FLAGS`
  (step 3), and in `CMAKE_EXE_LINKER_FLAGS` if you use the LTO build above.

  **A Cortex-A55 build is for RK3566 only.** It can use CPU instructions that the
  Cortex-A35 does not have, so expect illegal-instruction crashes on RK3326 devices.

  Pirry did not test or publish RK3566 builds. A contributor reports that it runs on a
  Powkiddy RGB30 with dArkOS and saw a small gain in one title, see
  [PR #3](https://github.com/pirrypirrypirry/yabasanshiro-pirry/pull/3).



## License

GPL-2.0-or-later, like Yaba Sanshiro and Yabause; see [LICENSE](LICENSE). Third-party components and their licenses are listed in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
