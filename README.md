# YabaSanshiro H700

This is [@D4n1984](https://github.com/D4n1984)'s H700 adaptation of [Pirry's fork](https://github.com/pirrypirrypirry/yabasanshiro-pirry), targeting RG34XXSP with muOS. It is a standalone AArch64 Sega Saturn emulator using the SH-2 dynarec and EGL/OpenGL ES 3. Download the ready-to-install muOS package from [Releases](https://github.com/D4n1984/yabasanshiro-h700/releases/latest).

The repository does not contain binaries, BIOS files, ROMs or save states. See the [muOS package guide](packaging/muos-h700/README.md) for installation and limitations.

## Apoyar el proyecto

Si quieres apoyar el trabajo, puedes hacerlo en [Buy Me a Coffee](https://buymeacoffee.com/danielgarciagarcia).

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

## License

GPL-2.0-or-later, like Yaba Sanshiro and Yabause; see [LICENSE](LICENSE). Third-party components and their licenses are listed in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
