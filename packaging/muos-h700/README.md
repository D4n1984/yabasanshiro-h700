# YabaSanshiro H700 para muOS

Este paquete contiene el ejecutable independiente `yabasanshiro-h700` y su lanzador. Su arranque y enlace de bibliotecas se han verificado en una RG34XXSP con muOS 2606.0 Andromeda, glibc 2.44 y GLIBCXX_3.4.32. También se ha comprobado el arranque de Grandia desde su M3U y la llegada de las pulsaciones de cruceta al mando Saturn emulado. La compatibilidad y el rendimiento en otros juegos requieren pruebas. No incluye BIOS ni juegos.

La versión corregida importa las asignaciones SDL del mando de muOS cuando
no existe una configuración de EmulationStation. Una configuración anterior
con todos los botones sin asignar se guarda como `keymapv2.json.broken` y se
regenera; las configuraciones existentes con botones asignados se conservan.
La importación admite botones y crucetas de tipo hat. Las asignaciones
digitales basadas en ejes requieren configuración manual.
Menu (Guide en SDL) y Select abren el menú del emulador; Select+Start permite
salir. El stick izquierdo se traduce a direcciones cuando se usa el pad digital.

## Instalación y ejecución por SSH

El binario generado con el SDK indicado requiere AArch64, glibc 2.38 o
posterior y `libstdc++.so.6` con `GLIBCXX_3.4.30` (GCC 12) o posterior.
También necesita `libSDL2-2.0.so.0`, `libEGL.so.1`, `libGLESv2.so.2` y
`libz.so.1`. No instale bibliotecas de otra distribución para sustituir las
del firmware. La prueba local bajo QEMU valida el arranque con el sysroot
del SDK, pero no el entorno gráfico ni las bibliotecas reales de su muOS.

Copie `run-game.sh` y el binario `yabasanshiro-h700` en un directorio persistente de la tarjeta, por ejemplo `/mnt/mmc/MUOS/emulator/yabasanshiro-h700`. Ajuste la ruta a la ubicación real de su almacenamiento. Conéctese por SSH y ejecute:

```sh
cd /mnt/mmc/MUOS/emulator/yabasanshiro-h700
chmod +x run-game.sh yabasanshiro-h700
./yabasanshiro-h700 -v
./run-game.sh '/ruta/a/Saturn/Juego.chd'
# También admite rutas a archivos .cue o listas .m3u.
```

Para usar una BIOS propia, legible desde el dispositivo:

```sh
YABASANSHIRO_BIOS='/ruta/a/mi-bios.bin' ./run-game.sh '/ruta/a/Saturn/Juego.cue'
```

Sin esa variable se usa la BIOS emulada. Las rutas absolutas de juego y BIOS deben tener menos de 256 bytes. Las partidas y configuración se guardan en `home/.yabasanshiro` dentro del directorio del paquete; `logs/last-run.log` se sustituye en cada ejecución. El lanzador requiere que ese directorio sea escribible.

Al abrir una lista M3U, el registro indica la ruta del primer disco resuelta
respecto a la carpeta de la lista. Las listas vacías, los discos inaccesibles
y las rutas resueltas demasiado largas se rechazan con un mensaje explícito.
La comprobación realizada cubre el arranque del primer disco, no un cambio de
disco durante una partida.

El programa utiliza SDL2 y las bibliotecas gráficas instaladas en muOS: no incluya bibliotecas SDL ni Mali de otra distribución. El lanzador no fuerza `SDL_VIDEODRIVER`; conserva la configuración del entorno y selecciona las bibliotecas `libEGL.so.1` y `libGLESv2.so.2` del sistema si existen en las rutas habituales. Se pueden definir `SDL_VIDEO_EGL_DRIVER` y `SDL_VIDEO_GL_DRIVER` para elegir rutas explícitas. La disponibilidad real de GLES 3 y la compatibilidad ABI del ejecutable deben comprobarse en el dispositivo. Una sesión SSH por sí sola puede carecer del entorno gráfico necesario; utilice el adaptador solo después de comprobar la versión de muOS.

## Integración con Andromeda 2606.0

`ext-yabasanshiro-h700.sh` (o `ext-yabasanshiro-h700-lto.sh` para la variante LTO) carga el entorno SDL y recibe el juego como tercer argumento, igual que los lanzadores del firmware. Por defecto usa `/mnt/mmc/MUOS/emulator/yabasanshiro-h700` y la BIOS existente `/run/muos/storage/bios/saturn_bios.bin`, si está disponible. `YABASANSHIRO_DIR` y `YABASANSHIRO_BIOS` permiten elegir otras rutas.

Para integrar el emulador en una instalación compatible, instale el adaptador en `/opt/muos/script/launch/ext-yabasanshiro-h700.sh` y añada una entrada a `Sega Saturn.external` en el manifiesto de usuario `/mnt/mmc/MUOS/info/manifest/core.json`: clave `yabasanshiro-h700`, nombre `YabaSanshiro H700`, core `ext-yabasanshiro-h700` y launcher `yabasanshiro-h700.sh`. Es un emulador independiente, no un core Libretro `.so`. Guarde una copia del manifiesto antes de editarlo.

Una copia personalizada de `MUOS/info/manifest/core.json` sustituye el manifiesto completo, por lo que debe partir del archivo completo de su instalación. La versión comprobada busca los adaptadores en `/opt/muos/script/launch`; `MUOS/info/launch` sirve para accesos directos a carpetas, no para estos scripts. Las rutas y el formato del manifiesto pueden cambiar al actualizar muOS: conserve el paquete y vuelva a integrar la entrada sobre el manifiesto actualizado cuando sea necesario.

### Mantener una variante LTO separada

La compilación con `-DYAB_ENABLE_LTO=ON` también genera un archivo llamado
`output/yabasanshiro-h700`. Para conservar ambas variantes, mantenga el
ejecutable normal en el directorio principal y copie el ejecutable LTO a
`variants/yabasanshiro-h700-lto` dentro de ese mismo directorio. Dé permiso
de ejecución a ambos archivos.

Instale `ext-yabasanshiro-h700-lto.sh` junto al adaptador normal en
`/opt/muos/script/launch`. La entrada adicional del manifiesto debe usar
la clave `yabasanshiro-h700-lto`, el core `ext-yabasanshiro-h700-lto` y el
launcher `yabasanshiro-h700-lto.sh`. Ambas variantes comparten configuración
y partidas en `home/.yabasanshiro`.

## Si una M3U no llega al lanzador

muOS puede dar prioridad a reglas por juego de `/opt/muos/share/info/override`. Si una regla existente limita los emuladores admitidos, revise su lógica y adapte la selección para delegar en `ext-yabasanshiro-h700`, conservando las rutas anteriores y una copia del archivo original.

## Compilación y fuentes

Consulte las instrucciones H700 del [repositorio](https://github.com/D4n1984/yabasanshiro-h700). `scripts/build-h700.sh` genera el ejecutable y prepara el paquete; sus opciones incluyen `BUILD_DIR`, `JOBS` y LTO opcional. La [página de releases](https://github.com/D4n1984/yabasanshiro-h700/releases) es el destino previsto para futuras versiones. El repositorio no incluye binarios, BIOS, ROM ni partidas guardadas. El proyecto se distribuye bajo GPL-2.0-or-later; consulte `LICENSE` y `THIRD-PARTY-NOTICES.md` para los créditos y licencias.

## Migración de una instalación anterior

Con el emulador cerrado, copie `home/.yabasanshiro` desde el directorio de la instalación anterior `yabasanshiro-pirry` al directorio del nuevo paquete para conservar partidas y configuración. Mantenga intactos los datos originales hasta comprobar la copia.

## Créditos

La adaptación H700 es de D4n1984. Gracias a Pirry por su fork y sus mejoras, a devMiyax por Yaba Sanshiro y al equipo de Yabause por el emulador original y a sus respectivos colaboradores.
