
## Platform

MS Windows only. It may be possible to adapt the software to other platforms.

## Hardware dependencies

Iromlab was created to be used in conjuction with Acronova Nimbie disc autoloaders. It has been tested with the [Nimbie NB21-DVD model](http://www.acronova.com/product/auto-blu-ray-duplicator-publisher-ripper-nimbie-usb-nb21/9/review.html). It may work with other models as well.

## Wrapped software

* [IsoBuster](https://www.isobuster.com/)
* [cd-info](https://linux.die.net/man/1/cd-info) - this tool is part of [libcdio](https://www.gnu.org/software/libcdio/),  the "GNU Compact Disc Input and Control Library".
* dBpoweramp, dBpoweramp Batch Ripper and Nimbie Batch Ripper Driver; all available [from the dBpoweramp website](https://www.dbpoweramp.com/batch-ripper.htm). (Note: Iromlab wraps dBpoweramp's Nimbie driver binaries to control the disc loading / unloading process)

 
## Obtaining and installing *cd-info* binaries

The installation of *cd-info* on windows is a bit tricky, mainly for 2 reasons:

1. There don't appear to be any ready-to-use Windows binaries
2. Compilation from source also has several issues under Windows

Binaries *do* exist for the [MSYS2/MingW](https://en.wikipedia.org/wiki/MinGW) environment; however these binaries are dynamically compiled and require a number of [dynamic link libraries](https://en.wikipedia.org/wiki/Dynamic-link_library) (DLLs) that are part of MSYS2 which are not available on a typical Windows system. So obtaining the binaries with their dependencies involves a number of steps:

1. install the MSYS2 environment
2. install libcdio with the MSYS2 package manager
3. locate the cd-info binary (cd-info.exe)
4. identify the DLLs needed by cd-info.exe
5. copy cd-info.exe and all required DLLs

Step by step instructions:

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

## External libraries

Iromlab uses a number of modules that are not part of Python's standard library, and which need to be installed separately:

* [requests](https://pypi.python.org/pypi/requests). Installation:

        (python -m ) pip install requests
    
* [wmi](https://pypi.python.org/pypi/WMI/). Installation:

        (python -m) pip install wmi

Finally Iromlab uses [tkInter](https://wiki.python.org/moin/TkInter), but this is included by default in the Python 2.7 / 3.x Windows installers.
        
## IsoBuster configuration

Before using Iromlab, it is necessary to change some of IsoBuster's default settings. This is mainly to avoid pop-up dialogs during that need user input during the imaging process. You only need to do this once; the changes will persist after upgrading IsoBuster to a newer version. Below instructions apply to IsoBuster 3.9 (Professional license).

### Disable all devices that are not optical drives 

From the IsoBuster GUI, go to the *Options* menu and then select *Communication*. From there select the *Finding Devices* tab, and uncheck the "Find and list other devices (HD, Flash, USB etc)" checkbox. Also make sure that the "Store this setting and use it always" checkbox at the bottom of the tab is checked. See screenshot below:

![](./findingDevices.png)

**Why:** by default IsoBuster tries to find and access all storage devices that are connected to the machine it runs on. This triggers a Windows "User Account Control" notification popup window (which needs manual intervention) every time IsoBuster is called from Iromlab. This can be prevented by disabling all devices except optical drives.

### Disable cue sheet and checksum creation

From the IsoBuster GUI, go to *Options* / *Image Files*, and then select the *General* tab. Locate the option "select when a cue sheet file will be created", and select "Never". Likewise, set the "Select when an MD5 checksum file will be created" setting to "Never". See screenshot:

![](cuesheetOption.png) 

**Why:** cue sheets aren't needed for ISO images, and we don't want IsoBuster to prompt for anything either. Iromlab already has built-in checksum creation functionality, so we don't need IsoBuster for this.

## Iromlab configuration

Example:

    <?xml version="1.0"?>
    <!-- iromlab configuration file. This file MUST be in the same directory 
    as iromlab.py/ iromlab.exe! 
    -->

    <config>

    <!-- IMPORTANT: do not wrap any of the file paths below in quotes, even if they contain
    spaces (the Python os.path libs don't seem to like this!)
    -->

    <!-- CD drive letter -->
    <cdDriveLetter>I</cdDriveLetter>

    <!-- root directory - this is the default search path for creating / opening batches -->
    <rootDir>E:\nimbieTest</rootDir>

    <!-- directory for storing temporary files -->
    <tempDir>C:\Temp</tempDir>

    <!-- prefix that is used to create batch names -->
    <prefixBatch>kb</prefixBatch>

    <!-- maximum number of seconds that iromlab will wait while trying to load a new disc 
    this will prevent iromlab from entering an infinite loop if e.g. a disc cannot be loaded
    properly because its is badly damaged
    -->
    <secondsToTimeout>20</secondsToTimeout>

    <!-- Below items point to the locations of all executables that are wrapped by Iromlab
    -->

    <!-- location of Nimbie drivers -->
    <prebatchExe>C:\Program Files\dBpoweramp\BatchRipper\Loaders\Nimbie\Pre-Batch\Pre-Batch.exe</prebatchExe>
    <loadExe>C:\Program Files\dBpoweramp\BatchRipper\Loaders\Nimbie\Load\Load.exe</loadExe>
    <unloadExe>C:\Program Files\dBpoweramp\BatchRipper\Loaders\Nimbie\Unload\Unload.exe</unloadExe>
    <rejectExe>C:\Program Files\dBpoweramp\BatchRipper\Loaders\Nimbie\Reject\Reject.exe</rejectExe>

    <!-- location of cd-info -->
    <cdInfoExe>C:\cdio\cd-info.exe</cdInfoExe>
    <!-- location of isoBuster -->
    <isoBusterExe>C:\Program Files (x86)\Smart Projects\IsoBuster\IsoBuster.exe</isoBusterExe>

    </config>


## Contributors

Written by Johan van der Knijff, except *sru.py* which was adapted from the [KB Python API](https://github.com/KBNLresearch/KB-python-API) which is written by WillemJan Faber. The KB Python API is released under the GNU GENERAL PUBLIC LICENSE.
