#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS adaptation by D4n1984.
# Adapter for the Andromeda external emulator launch convention.
. /opt/muos/script/var/stage.sh
. /opt/muos/script/var/display.sh
. /opt/muos/script/var/launch.sh

SETUP_STAGE_OVERLAY
SETUP_SDL_ENVIRONMENT

APP_DIR=${YABASANSHIRO_DIR:-/mnt/mmc/MUOS/emulator/yabasanshiro-h700}
if [ -z "${YABASANSHIRO_BIOS:-}" ] && [ -r /run/muos/storage/bios/saturn_bios.bin ]; then
    YABASANSHIRO_BIOS=/run/muos/storage/bios/saturn_bios.bin
    export YABASANSHIRO_BIOS
fi
PROCESS_NAME=${YABASANSHIRO_BIN:-yabasanshiro-h700}
SET_VAR "system" "foreground_process" "${PROCESS_NAME##*/}"
exec "$APP_DIR/run-game.sh" "$FILE"
