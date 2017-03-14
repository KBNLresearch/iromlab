
## Installation
    
    (python -m) pip install iromlab

## Platform

MS Windows only. It may be possible to adapt the software to other platforms.

## Hardware dependencies

Iromlab was created to be used in conjuction with Acronova Nimbie disc autoloaders. It has been tested with the [Nimbie NB21-DVD model](http://www.acronova.com/product/auto-blu-ray-duplicator-publisher-ripper-nimbie-usb-nb21/9/review.html). It may work with other models as well.

## Wrapped software

Iromlab wraps around a number of existing software tools:

* [IsoBuster](https://www.isobuster.com/)
* dBpoweramp, dBpoweramp Batch Ripper and Nimbie Batch Ripper Driver; all available [from the dBpoweramp website](https://www.dbpoweramp.com/batch-ripper.htm). (Note: Iromlab wraps dBpoweramp's Nimbie driver binaries to control the disc loading / unloading process.
* dBpoweramp command-line ripping tool, which provides a command-line interface to dBpoweramp's ripper. Custom tool developed specially for KB, not included in dBpoweramp default installer!
* [cd-info](https://linux.die.net/man/1/cd-info) - this tool is part of [libcdio](https://www.gnu.org/software/libcdio/),  the "GNU Compact Disc Input and Control Library".
* [shntool](http://www.etree.org/shnutils/shntool/) - used to verify the integrity of created WAVE files.
* [flac](https://xiph.org/flac/) - used to verify the integrity of created WAVE files.

Both IsoBuster and dBpoweramp require a license, and they must be installed separately. Binaries of cd-info, shntool and flac are included in the iromlab installation. When Iromlab is started for the first time, they are automatically copied to directory `iromlab/tools' in the Windows user directory.
        
## [Isobuster setup and configuration](./setupIsobuster.md)

## [dBpoweramp setup and configuration](./setupDbpoweramp.md)


## Iromlab configuration

Example:

    <?xml version="1.0"?>
    <!-- iromlab configuration file. This file MUST be in the same directory 
    as iromlab.py/ iromlab.exe! 
    -->

    <config>

    <!-- IMPORTANT notes on file paths:

    1. Do not wrap any of the file paths below in quotes, even if they contain
       spaces! (the Python os.path libs don't seem to like this!)
    2. Only use FORWARD SLASHES; backslashes can lead to unexpected behavior because
       Python can see them as escape characters.
    -->

    <!-- CD drive letter -->
    <cdDriveLetter>I</cdDriveLetter>

    <!-- root directory - this is the default search path for creating / opening batches -->
    <rootDir>E:/nimbieTest</rootDir>

    <!-- directory for storing temporary files -->
    <tempDir>C:/Temp</tempDir>

    <!-- prefix that is used to create batch names -->
    <prefixBatch>kb</prefixBatch>
    
    <!-- String that sets audio format. Permitted values: wav or flac. ONLY used for the audio verification, 
    the ripping format must be set from dBpoweramp's CD Ripper tool (GUI) defined in the Windows registry  -->
    <audioFormat>flac</audioFormat>

    <!-- maximum number of seconds that iromlab will wait while trying to load a new disc 
    this will prevent iromlab from entering an infinite loop if e.g. a disc cannot be loaded
    properly because its is badly damaged
    -->
    <secondsToTimeout>20</secondsToTimeout>

    <!-- Below items point to the locations of all executables that are wrapped by Iromlab
    -->

    <!-- location of Nimbie drivers -->
    <prebatchExe>C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Pre-Batch/Pre-Batch.exe</prebatchExe>
    <loadExe>C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Load/Load.exe</loadExe>
    <unloadExe>C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Unload/Unload.exe</unloadExe>
    <rejectExe>C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Reject/Reject.exe</rejectExe>

    <!-- location of isoBuster -->
    <isoBusterExe>C:/Program Files (x86)/Smart Projects/IsoBuster/IsoBuster.exe</isoBusterExe>

    <!-- location of dBpoweramp console ripper -->
    <dBpowerampConsoleRipExe>C:/Program Files/dBpoweramp/kb-nl-consolerip.exe</dBpowerampConsoleRipExe>

    </config>
