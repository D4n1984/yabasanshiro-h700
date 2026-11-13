#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS installation by D4n1984.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/install-muos.py"
