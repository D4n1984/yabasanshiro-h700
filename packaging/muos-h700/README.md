# YabaSanshiro H700 para muOS

Emulador independiente para RG34XXSP con muOS. Se ha verificado el arranque en muOS 2606.0 Andromeda, glibc 2.44 y GLIBCXX_3.4.32; la compatibilidad y el rendimiento varían entre juegos. Requiere Linux AArch64, glibc 2.38 o posterior y `GLIBCXX_3.4.30` o posterior, Python 3 y las bibliotecas SDL2, EGL, GLES y zlib de muOS. La BIOS y los juegos no están incluidos: coloque su propia BIOS en la ubicación habitual de muOS (`/run/muos/storage/bios/saturn_bios.bin`) o use la BIOS emulada.

## Instalación

1. Haga una copia de seguridad de sus partidas y del manifiesto personalizado antes de empezar. Cierre el juego y cualquier emulador.
2. Extraiga el ZIP y copie mediante SFTP la carpeta completa `yabasanshiro-h700` a `/mnt/mmc/MUOS/emulator/`. El instalador requiere exactamente esa ubicación. Conserve `variants/` y los demás archivos del paquete.
3. Active SSH en muOS, conecte desde su ordenador con `ssh root@<IP-DE-LA-CONSOLA>` y ejecute como root:

   ```sh
   sh /mnt/mmc/MUOS/emulator/yabasanshiro-h700/install.sh
   ```

4. Vuelva al menú de contenidos de muOS y abra la asignación de emulador de
   su juego o carpeta de Sega Saturn. Seleccione **YabaSanshiro H700** o
   **YabaSanshiro H700 (LTO)**. Si las entradas nuevas no aparecen, reinicie
   el menú o la consola.

El instalador comprueba ambos ejecutables y registra **YabaSanshiro H700** y **YabaSanshiro H700 (LTO)** como emuladores externos para Sega Saturn. No cambia el emulador predeterminado. Guarda copias versionadas del manifiesto y de los adaptadores anteriores en `backups/` dentro de la carpeta del paquete. No modifica bibliotecas, BIOS, juegos ni reglas individuales de juego. Si el manifiesto personalizado está dañado, la instalación se detiene para evitar sobrescribirlo. Ambos ejecutables comparten configuración y partidas.

Si existe una instalación anterior en `yabasanshiro-pirry` y el nuevo paquete aún no tiene directorio `home`, se copia el `home` anterior; los datos originales se conservan. Si ya existe `home`, se deja intacto. Compruebe la copia antes de retirar ninguna instalación anterior. Las partidas y la configuración se guardan en `home/.yabasanshiro`.

El adaptador usa la BIOS de muOS si está disponible; `YABASANSHIRO_BIOS` permite seleccionar otra. Sin ella se usa la BIOS emulada. Las rutas absolutas de juego y BIOS deben tener menos de 256 bytes. Se admiten CHD, CUE y listas M3U; una lista vacía, una ruta demasiado larga o un disco inaccesible se rechazan. Se ha probado el arranque del primer disco, no el cambio de disco durante una partida.

El programa importa las asignaciones SDL de muOS cuando no existe configuración de EmulationStation. Admite botones y crucetas tipo hat; las asignaciones digitales basadas en ejes requieren configuración manual. Menu o Select abren el menú, Select+Start permite salir y el stick izquierdo se traduce a direcciones con el pad digital.

## Fuentes y créditos

El código y las instrucciones de compilación están en [D4n1984/yabasanshiro-h700](https://github.com/D4n1984/yabasanshiro-h700). `scripts/build-h700.sh` permite compilar las variantes normal y LTO. El proyecto se distribuye bajo GPL-2.0-or-later; consulte `LICENSE` y `THIRD-PARTY-NOTICES.md`. Adaptación H700 por D4n1984, con agradecimientos a Pirry, devMiyax y al equipo de Yabause y sus colaboradores.

## Apoyar el proyecto

Si quieres apoyar el trabajo, puedes hacerlo en [Buy Me a Coffee](https://buymeacoffee.com/danielgarciagarcia).
