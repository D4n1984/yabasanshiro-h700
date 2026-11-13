#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS installation by D4n1984.
"""Install the standalone H700 launchers into muOS Andromeda."""
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

APP = Path('mnt/mmc/MUOS/emulator/yabasanshiro-h700')
OLD = Path('mnt/mmc/MUOS/emulator/yabasanshiro-pirry')
CUSTOM = Path('mnt/mmc/MUOS/info/manifest/core.json')
BUNDLE = Path('opt/muos/share/info/manifest/core.json')
LAUNCH = Path('opt/muos/script/launch')
ADAPTERS = ('ext-yabasanshiro-h700.sh', 'ext-yabasanshiro-h700-lto.sh')
BINARIES = ('yabasanshiro-h700', 'variants/yabasanshiro-h700-lto')


def active_emulator(root):
    proc = root / 'proc'
    if not proc.is_dir():
        raise RuntimeError('No se puede inspeccionar /proc')
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        names = []
        try:
            names.append(os.path.basename(os.readlink(entry / 'exe')))
        except OSError:
            pass  # processes may exit while /proc is being scanned
        try:
            cmdline = (entry / 'cmdline').read_bytes().split(b'\0')
            names.extend(os.path.basename(os.fsdecode(x)) for x in cmdline[:1])
        except OSError:
            pass
        if any(name.lower().startswith('yabasanshiro') or name.lower() in
               ('muxretro', 'retroarch', 'yabadabadoo') for name in names):
            return True
    return False


def probe(binary):
    with tempfile.TemporaryDirectory(prefix='yabasanshiro-probe-') as home:
        executable = Path(home) / binary.name
        shutil.copyfile(binary, executable)
        executable.chmod(0o755)
        env = os.environ.copy()
        env.update(HOME=home, LD_BIND_NOW='1')
        result = subprocess.run([str(executable), '-v'], env=env, timeout=30,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if result.returncode:
            reason = result.stderr.decode('utf-8', errors='replace').strip()
            raise RuntimeError(binary.name + ': ' + (reason or 'no se puede ejecutar este binario'))


def atomic_write(path, content, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.yabasanshiro-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def install(root, package_path, probe_callback=probe):
    root, package = Path(root), Path(package_path)
    app = root / APP
    if package.resolve() != app.resolve():
        raise RuntimeError('Copie el paquete completo a /mnt/mmc/MUOS/emulator/yabasanshiro-h700 antes de instalar')
    for name in ('stage.sh', 'display.sh', 'launch.sh'):
        if not (root / 'opt/muos/script/var' / name).is_file():
            raise RuntimeError('Falta el entorno de muOS Andromeda: ' + name)
    if not (root / LAUNCH).is_dir() or not (root / BUNDLE).is_file():
        raise RuntimeError('Faltan el directorio de lanzadores o el manifiesto de muOS')
    if active_emulator(root):
        raise RuntimeError('Cierre los emuladores antes de instalar')
    for name in (*BINARIES, 'run-game.sh', *ADAPTERS):
        if not (package / name).is_file():
            raise RuntimeError('Falta en el paquete: ' + name)
    custom, bundle = root / CUSTOM, root / BUNDLE
    source = custom if custom.exists() else bundle
    try:
        manifest = json.loads(source.read_text(encoding='utf-8'))
        external = manifest['Sega Saturn']['external']
        if not isinstance(external, dict):
            raise ValueError('Sega Saturn.external no es un objeto')
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RuntimeError('Manifiesto inválido: ' + str(error)) from error
    for binary in BINARIES:
        probe_callback(package / binary)
    for suffix in ('', '-lto'):
        external['yabasanshiro-h700' + suffix] = {
            'name': 'YabaSanshiro H700' + (' (LTO)' if suffix else ''),
            'core': 'ext-yabasanshiro-h700' + suffix,
            'launcher': 'yabasanshiro-h700' + suffix + '.sh',
            'governor': 'performance', 'extra': 0,
        }
    data = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    # A unique backup directory preserves all prior installer runs.
    backup_base = app / 'backups'
    backup_base.mkdir(parents=True, exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix=datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=backup_base))
    if custom.exists():
        shutil.copy2(custom, backup / 'core.json')
    else:
        shutil.copy2(bundle, backup / 'core.bundle.json')
    for name in ADAPTERS:
        target = root / LAUNCH / name
        if target.exists():
            shutil.copy2(target, backup / name)
    home, old_home = app / 'home', root / OLD / 'home'
    if not home.exists() and old_home.is_dir():
        shutil.copytree(old_home, home)
    for name in (*BINARIES, 'run-game.sh', *ADAPTERS):
        (package / name).chmod(0o755)
    for name in ADAPTERS:
        atomic_write(root / LAUNCH / name, (package / name).read_bytes(), 0o755)
    atomic_write(custom, data, 0o644)
    return backup


def main():
    if platform.system() != 'Linux' or platform.machine().lower() not in ('aarch64', 'arm64'):
        raise RuntimeError('Se necesita Linux AArch64')
    if os.geteuid() != 0:
        raise RuntimeError('Ejecute el instalador como root')
    backup = install(Path('/'), Path(__file__).resolve().parent)
    print('Instalación completada. Copia de seguridad:', backup)


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print('Instalación abortada:', error, file=sys.stderr)
        sys.exit(1)
