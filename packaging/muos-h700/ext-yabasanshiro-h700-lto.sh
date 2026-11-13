#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS adaptation by D4n1984.
# Keep the tested binary and saves shared; only select the experimental binary.
APP_DIR=${YABASANSHIRO_DIR:-/mnt/mmc/MUOS/emulator/yabasanshiro-h700}
YABASANSHIRO_BIN="$APP_DIR/variants/yabasanshiro-h700-lto"
export YABASANSHIRO_BIN
exec /opt/muos/script/launch/ext-yabasanshiro-h700.sh "$@"
