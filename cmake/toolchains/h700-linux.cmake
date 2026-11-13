# SPDX-License-Identifier: GPL-2.0-or-later
# H700 / muOS adaptation by D4n1984.
# Cross-compile with the Knulli H700 SDK (run its relocate-sdk.sh first).
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(H700_SDK "$ENV{H700_SDK}" CACHE PATH "Relocated H700 SDK directory")
if(NOT EXISTS "${H700_SDK}/bin/aarch64-buildroot-linux-gnu-gcc")
    message(FATAL_ERROR "Set H700_SDK to the extracted, relocated H700 SDK")
endif()
set(CMAKE_C_COMPILER "${H700_SDK}/bin/aarch64-buildroot-linux-gnu-gcc")
set(CMAKE_CXX_COMPILER "${H700_SDK}/bin/aarch64-buildroot-linux-gnu-g++")
set(CMAKE_ASM_COMPILER "${CMAKE_C_COMPILER}")
set(CMAKE_AR "${H700_SDK}/bin/aarch64-buildroot-linux-gnu-gcc-ar")
set(CMAKE_RANLIB "${H700_SDK}/bin/aarch64-buildroot-linux-gnu-gcc-ranlib")
set(CMAKE_STRIP "${H700_SDK}/bin/aarch64-buildroot-linux-gnu-strip")
execute_process(COMMAND "${CMAKE_C_COMPILER}" -print-sysroot
    OUTPUT_VARIABLE CMAKE_SYSROOT OUTPUT_STRIP_TRAILING_WHITESPACE
    COMMAND_ERROR_IS_FATAL ANY)
set(CMAKE_FIND_ROOT_PATH "${CMAKE_SYSROOT}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
set(ENV{PKG_CONFIG_SYSROOT_DIR} "${CMAKE_SYSROOT}")
set(ENV{PKG_CONFIG_LIBDIR} "${CMAKE_SYSROOT}/usr/lib/pkgconfig:${CMAKE_SYSROOT}/usr/share/pkgconfig")
set(ENV{PKG_CONFIG_PATH} "")
set(CMAKE_C_FLAGS_INIT "-O3 -mcpu=cortex-a53 -mtune=cortex-a53 -fno-strict-aliasing -D_GNU_SOURCE -Wno-implicit-function-declaration -Wno-incompatible-pointer-types -Wno-int-conversion")
set(CMAKE_CXX_FLAGS_INIT "-O3 -mcpu=cortex-a53 -mtune=cortex-a53 -fno-strict-aliasing -D_GNU_SOURCE")
