# Iromlab setup and configuration

## Installation

The recommended way to install Iromlab is to use *pip*. Installing with *pip* will also automatically install any Python packages that are used by Iromlab. On Windows systems the *pip* executable is located in the *Scripts* directory which is located under Python's top-level installation folder (e.g. *C:\Python36\Scripts*). To install Iromlab, follow the steps below:

1. Launch a Command Prompt window. Depending on your system settings you may need to do this with Administrator privilege (right-click on the *Command Prompt* icon and the choose *Run as Administrator*).
2. Type:

      `%path-to-pip%\pip install iromlab`
   
    Here, replace %path-to-pip% with the actual file bpath on your system. For example:

     `C:\Python36\Scripts\pip install iromlab`
    
The above steps will install Iromlab and all required libraries. It also installs Windows binaries of the following tools:

* [cd-info](https://linux.die.net/man/1/cd-info) - this tool is part of [libcdio](https://www.gnu.org/software/libcdio/),  the "GNU Compact Disc Input and Control Library".
* [shntool](http://www.etree.org/shnutils/shntool/) - used to verify the integrity of created WAVE files.
* [flac](https://xiph.org/flac/) - used to verify the integrity of created WAVE files.

Finally it also creates a shortcut to the main Iromlab application on the Windows Desktop.
        

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

| |
|:--|
|[Back to Setup Guide](./setupGuide.md)|