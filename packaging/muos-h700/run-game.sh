#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS adaptation by D4n1984.
# Run from persistent user storage with the muOS libraries already installed.
set -eu

if [ "$#" -ne 1 ]; then
    echo "Uso: $0 /ruta/al/juego.chd|cue|m3u" >&2
    exit 2
fi

GAME_DIR=$(CDPATH= cd -- "$(dirname -- "$1")" && pwd -P) || exit 1
GAME="$GAME_DIR/$(basename -- "$1")"
if [ ! -f "$GAME" ] || [ ! -r "$GAME" ]; then
    echo "No se puede leer el juego: $GAME" >&2
    exit 1
fi

APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P) || exit 1
BIN=${YABASANSHIRO_BIN:-$APP_DIR/yabasanshiro-h700}
if [ ! -x "$BIN" ]; then
    echo "No se encuentra el ejecutable o no tiene permiso de ejecución: $BIN" >&2
    exit 1
fi

# The emulator stores ROM and BIOS paths in 256-byte buffers.
export LC_ALL=C
if [ "${#GAME}" -ge 256 ]; then
    echo "La ruta del juego supera el límite de 255 bytes." >&2
    exit 1
fi
if [ -n "${YABASANSHIRO_BIOS:-}" ]; then
    BIOS_DIR=$(CDPATH= cd -- "$(dirname -- "$YABASANSHIRO_BIOS")" && pwd -P) || exit 1
    BIOS="$BIOS_DIR/$(basename -- "$YABASANSHIRO_BIOS")"
    if [ ! -f "$BIOS" ] || [ ! -r "$BIOS" ] || [ "${#BIOS}" -ge 256 ]; then
        echo "BIOS inaccesible o ruta de 256 bytes o más: $BIOS" >&2
        exit 1
    fi
fi

HOME="$APP_DIR/home"
export HOME
mkdir -p "$HOME" "$APP_DIR/logs"

# main.cpp otherwise requests unversioned development names. Prefer the
# installed runtime sonames when present; preserve explicit user overrides.
if [ -z "${SDL_VIDEO_EGL_DRIVER:-}" ]; then
    for dir in /usr/lib /lib /usr/lib/aarch64-linux-gnu /lib/aarch64-linux-gnu; do
        if [ -e "$dir/libEGL.so.1" ]; then
            SDL_VIDEO_EGL_DRIVER="$dir/libEGL.so.1"
            export SDL_VIDEO_EGL_DRIVER
            break
        fi
    done
fi
if [ -z "${SDL_VIDEO_GL_DRIVER:-}" ]; then
    for dir in /usr/lib /lib /usr/lib/aarch64-linux-gnu /lib/aarch64-linux-gnu; do
        if [ -e "$dir/libGLESv2.so.2" ]; then
            SDL_VIDEO_GL_DRIVER="$dir/libGLESv2.so.2"
            export SDL_VIDEO_GL_DRIVER
            break
        fi
    done
fi

cd "$APP_DIR"
exec >"$APP_DIR/logs/last-run.log" 2>&1
printf '[launch] game=%s\n' "$GAME"
printf '[launch] binary=%s\n' "$BIN"
printf '[launch] bios=%s\n' "${YABASANSHIRO_BIOS:-HLE}"
if [ -n "${YABASANSHIRO_BIOS:-}" ]; then
    exec "$BIN" -i "$GAME" -b "$BIOS"
fi
exec "$BIN" -i "$GAME"
