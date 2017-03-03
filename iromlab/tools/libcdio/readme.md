All files in the win64 directory are 64-bit Windows binaries of the [libcdio](https://www.gnu.org/software/libcdio/) tools. Libcdio is released under the GNU general public license.

The installation of *cd-info* on windows is a bit tricky, mainly for 2 reasons:

1. There don't appear to be any ready-to-use Windows binaries
2. Compilation from source also has several issues under Windows

Binaries *do* exist for the [MSYS2/MingW](https://en.wikipedia.org/wiki/MinGW) environment; however these binaries are dynamically compiled and require a number of [dynamic link libraries](https://en.wikipedia.org/wiki/Dynamic-link_library) (DLLs) that are part of MSYS2 which are not available on a typical Windows system. 

Obtaining the binaries with their dependencies involves a number of steps:

1. install the MSYS2 environment
2. install libcdio with the MSYS2 package manager
3. locate the cd-info binary (cd-info.exe)
4. identify the DLLs needed by cd-info.exe
5. copy cd-info.exe and all required DLLs

The binaries in the win64 directory were obtained using the following procedure:

1. Download the MSYS2 installer at <https://msys2.github.io/> and install
2. Start an MSYS shell and run `autorebase.bat` (file exists in root of *mysys64* installation directory; not 100% sure if this step is necessary)
3. Use the pacman package manager to install the libcdio package:

        pacman -S mingw-w64-x86_64-libcdio

    After installation all binaries can be found in MSYS2 under *C:\msys64\mingw64\bin*. 
4. Find all dependencies of *cd-info.exe*:

        ldd cd-info.exe 

    Result:

        ntdll.dll => /c/Windows/SYSTEM32/ntdll.dll (0x77a70000)
        kernel32.dll => /c/Windows/system32/kernel32.dll (0x77950000)
        KERNELBASE.dll => /c/Windows/system32/KERNELBASE.dll (0x7fefd7c0000)
        libiso9660-10.dll => /c/MSYS64/Mingw64/bin/libiso9660-10.dll (0x6de80000)
        libcdio-16.dll => /c/MSYS64/Mingw64/bin/libcdio-16.dll (0x6d280000)
        msvcrt.dll => /c/Windows/system32/msvcrt.dll (0x7feff870000)
        USER32.dll => /c/Windows/system32/USER32.dll (0x77850000)
        GDI32.dll => /c/Windows/system32/GDI32.dll (0x7fefdd70000)
        LPK.dll => /c/Windows/system32/LPK.dll (0x7fefeec0000)
        USP10.dll => /c/Windows/system32/USP10.dll (0x7fefeca0000)
        WINMM.dll => /c/Windows/system32/WINMM.dll (0x7fefb240000)
        libiconv-2.dll => /c/MSYS64/Mingw64/bin/libiconv-2.dll (0x66000000)
        libcddb-2.dll => /c/MSYS64/Mingw64/bin/libcddb-2.dll (0x67f00000)
        WS2_32.dll => /c/Windows/system32/WS2_32.dll (0x7fefee70000)
        RPCRT4.dll => /c/Windows/system32/RPCRT4.dll (0x7fefeed0000)
        NSI.dll => /c/Windows/system32/NSI.dll (0x7feff0c0000)
        libsystre-0.dll => /c/MSYS64/Mingw64/bin/libsystre-0.dll (0x6bcc0000)
        libtre-5.dll => /c/MSYS64/Mingw64/bin/libtre-5.dll (0x63bc0000)
        libintl-8.dll => /c/MSYS64/Mingw64/bin/libintl-8.dll (0x61cc0000)
        ADVAPI32.dll => /c/Windows/system32/ADVAPI32.dll (0x7fefed70000)
        sechost.dll => /c/Windows/SYSTEM32/sechost.dll (0x7feff000000)

    All dependencies under *C/Windows* probably OK on a typical system, so need to watch for anything under *C/MSYS64/Mingw64/bin* (which is dir in which iso-info.exe resides). So:

        libiso9660-10.dll => /c/MSYS64/Mingw64/bin/libiso9660-10.dll (0x6de80000)
        libcdio-16.dll => /c/MSYS64/Mingw64/bin/libcdio-16.dll (0x6d280000)
        libiconv-2.dll => /c/MSYS64/Mingw64/bin/libiconv-2.dll (0x66000000)
        libcddb-2.dll => /c/MSYS64/Mingw64/bin/libcddb-2.dll (0x67f00000)
        libsystre-0.dll => /c/MSYS64/Mingw64/bin/libsystre-0.dll (0x6bcc0000)
        libtre-5.dll => /c/MSYS64/Mingw64/bin/libtre-5.dll (0x63bc0000)
        libintl-8.dll => /c/MSYS64/Mingw64/bin/libintl-8.dll (0x61cc0000)

     Copy all these files to same directory as *cd-info.exe*.
