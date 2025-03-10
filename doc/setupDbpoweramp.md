# dBpoweramp setup and configuration

## Installation

Download and install the following:

* dBPoweramp Reference, 64-bit version. You can purchase it [here](https://www.dbpoweramp.com/purchase.htm). Use the download link in the order details e-mail that you received from dBpoweramp after you purchased the software. 
* [dBpoweramp Batch Ripper](https://www.dbpoweramp.com/install/dBpoweramp-Batch-Ripper.exe)
* [Nimbie Batch Ripper Driver](https://www.dbpoweramp.com/install/dBpoweramp-Batch-Ripper-Nimbie.exe)

Finally, you need the *dBpoweramp* console ripping tool. This is a custom tool that was developed specifically for the KB, but Illustrate Ltd. agreed to make it publicly available with *Iromlab*. You can [download a 64-bit Windows executable here](https://github.com/KBNLresearch/iromlab/raw/master/dBpowerampconsolerip/kb-nl-consolerip.exe) . Drop the file in the same directory where the *CDGrab.exe* is located.  This is typically dBpoweramp's top-level installation folder (*C:\Program Files\dBpoweramp*). Drop the executable of the console riping tool (*kb-nl-consolerip.exe*) in this folder, as shown below:

![](./img/dbpaCLI.png)

## Drive configuration

After installing, locate the *dBpoweramp* item in the Windows Start Menu, and launch the *Batch Ripper - Configuration* application:

![](./img/dbpaBatchripperConfig.png)

Now the following window appears:

![](./img/dbpaBatchripperConfig2.png)
    
Under *Unconfigured Drives*, locate the Nimbie's drive select the CD-drive that corresponds to the Nimbie discrobot (make sure *not* to select the computer's built-in drive here; the Nimbie has a *Teac* drive so you should be able to identify it from its description). Click on *Configure* to the right-hand side of the drive.

Change *Loading Method* (top of the window) to *Nimbie* and then press *Configure Drive*:

![](./img/dbpaBatchripperConfig3.png)

If all went well the drive is now moved to the *Configured Drives* section on the opening screen. Press *OK* to close *Batch Ripper - Configuration*.

## Configure general settings

Locate the *dBpoweramp* item in the Windows Start Menu, and launch the *CD Ripper* application, as shown below: 

![](./img/dbpaCDripper.png)

This results in the following window:

![](./img/dbpaCDRipperWindow.png)

At the bottom you can configure a number of settings. Select the following:

* *Profile* - leave this at *(default)*
* *Rip to* - select either  *Wave* or *FLAC*
    * If you selected *Wave*, make sure the encoder settings (on the right) are set to *Uncompressed*, with *Bit Depth*, *Sample Rate* and *Channels* all at *as source*.
    * In case of *FLAC*, leave the *Lossless Encoding* setting at *Level 5*. (TODO: what about the *Verify Written Audio* checkbox?)
* Click on the *DSP* tab, and then on the *Add DSP / Action* button, and select *Add DSP Effect*:

    ![](./img/dbpaDSP1.png)
* Select *RePlayGain* from the drop-down list:

    ![](./img/dbpaReplayGain.png)
    
    (This option adds metadata on a track's loudness to the audio file. This information can be used by some audio players for volume matching / correcting. It doesn't change the audio itself.)
* *Path* - leave this at the default (whatever it may be).
* *Naming* - click on the *set* button, remove the default value, then click on the *Add Tag* button and select 'Track Number'. Press *OK* (the value of the *Naming* field now shows as *TrackNum*). The effect of this is that track numbers will be used as the base names of the audio files that are written (*001.wav*, *002.wav*, and so on).
* *CD Drive* - select the CD-drive that corresponds to the Nimbie discrobot (make sure *not* to select the computer's built-in drive here; the Nimbie has a *Teac* drive so you should be able to identify it from its description.)

The following sections are largely based on dBpoweramp's *CD Ripper Setup Guide*, which is part of dBpoweramp's documentation.

## Configure ripper options

Now click on the green menu button at the top toolbar, and select *CD Ripper Options*:

![](./img/dbpaRipperOptions.png)

In the window that appears, set *Ripping  Method* (at the top) to *Secure (Recover Errors)*:

![](./img/dbpaRipperOptions2.png)

Leave the *AccurateRip* options as they are (all options checked). Next click on *Secure Settings* (to the right of *Secure (Recover Errors)*):

![](./img/dbpaSecureOptions.png)

* Check *Enable Ultra Secure Ripping*
* *Minimum Ultra Passes* - set to 2 
* *Maximum Ultra Passes* - set to 4
*  *End After Clean Passes* - set to 2

Note: the above settings are valid for a drive that does not support C2 pointers. See dBpoweramp's *cd-ripper-setup-guide* on how to determine if a drive supports C2 pointers (the Nimbie's built-in drive doesn't appear to support them).

* *Drive Read Cache* - leave this at default value (1024 kB)
* *Clear Read Cache with FUA* - leave this unchecked
* *C2 Error Pointers for Error Detection* - leave this unchecked as well

## Secure Rip Abort options

Scrolling down we see the following options:

![](./img/dbpaSecureRipAbort.png)

* *After Unrecoverable Frames* - set to 1 frame
* *When have to Re-Rip* - set to 100 frames
* *After Ripping a Track For* - set to 10 minutes

<!-- Might be a bit short, esp. for CDs with very long tracks? -->

Also, check *Mark Track as Error if Insecure*, and check both the *Secure Extraction Log* options. 

## Log filename

Finally, click to the right of *Log Filename* and change the value to:

    [rippedtopath]\dbpoweramp.log

Note: you **must** use **exactly this name**, since otherwise [*omSipCreator*](https://github.com/KBNLresearch/omSipCreator) (which uses the file for provenance metadata) won't recognise it!
    
## AccurateRip configuration

AccurateRip is a technique that performs a [Cyclic Redundancy Check](https://en.wikipedia.org/wiki/Cyclic_redundancy_check) (CRC) of ripped audio tracks against an online database. This only works correctly if the read offset of the CD-drive is known. To so, follow the steps below:

1. Insert a (preferrably well-known/popular) audio CD into the disc robot's loader.
2. Load the CD using the *Load* command-line tool that is part of the Nimbie Batch Ripper Driver. It is typically located under `C:\Program Files\dBpoweramp\BatchRipper\Loaders\Nimbie\Load\`. To run it, open a Windows command prompt, and enter the following:

    `"C:\Program Files\dBpoweramp\BatchRipper\Loaders\Nimbie\Load\Load" --drive="I"`

    Make sure to replace "I" by the actual drive letter on your system.

3. Wait until the CD has loaded and you can see its details in the *CD Ripper* window.
4. Close *CD Ripper* and then re-start it.

    The following dialog will now pop up:

    ![](./img/dbpaAccurateRip.png)

    Press *Configure*. After a few seconds the result is:

    ![](./img/dbpaAccurateRip2.png)

    This value is automatically added to the CD-ROM settings:

    ![](./img/dbpaAccurateRip3.png)

    Press *OK* and then press the *Rip* button (top-left) to test the settings. Inspect the ripping information that is displayed once the CD is ripped. In particular, check if (most of) the tracks have an *accurate* status. If so, unload the CD by pressing the *Eject CD* button (directly to to the right of the *Rip* button). Alternatively you may also use the *Unload.exe* driver application from the command prompt for this, using:

    `"C:\Program Files\dBpoweramp\BatchRipper\Loaders\Nimbie\Unload\Unload" --drive="I"`
    
    Again, replace "I" by your actual drive letter here.

## Album art and metadata options

Go back to *CD Ripper Options* and click on *Options* next to *Meta Data & ID Tag*:

![](./img/dbpaMetaID.png)

Click to the right of *Write to [output folder]*, and select *None*. This will disable the writing of any artwork JPEGs to the output folder.

![](./img/dbpaAlbumArt.png)

Close the *CD Ripper* application. Now dBpoweramp is configured and ready for use! 


| | |
|:--|:--|
|[Back to Setup Guide](./setupGuide.md)|[>> Next: Iromlab setup and configuration](./setupIromlab.md)|
