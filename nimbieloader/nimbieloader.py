#! /usr/bin/env python
import sys
import os
import time
import imp
import glob
import codecs
import xml.etree.ElementTree as ETree
import config
import shared
import drivers
import win32api


def testDrive(letter):
    """
    Tests a given drive letter to see if the drive is question is ready for 
    access. This is to handle things like floppy drives and USB card readers
    which have to have physical media inserted in order to be accessed.
    Returns true if the drive is ready, false if not.
    Source: http://stackoverflow.com/a/1020363
    """
    returnValue = False
    # This prevents Windows from showing an error to the user, and allows python 
    # to handle the exception on its own.
    oldError = win32api.SetErrorMode(1) #note that SEM_FAILCRITICALERRORS = 1
    try:
    	freeSpace = win32api.GetDiskFreeSpaceEx(letter)
    except:
    	returnValue = False
    else:
    	returnValue = True
    # restore the Windows error handling state to whatever it was before we
    # started messing with it:
    win32api.SetErrorMode(oldError)
    return(returnValue)
    
def getCarrierInfo():
    # Determine carrier type and number of sessions on carrier
    # cd-info command line:
    # cd-info -C d: --no-header --no-device-info --no-cddb --dvd
    
    args = [config.cdInfoExe]
    args.append( "-C")
    args.append("".join([config.cdDriveLetter, ":"]))
    args.append("--no-header")
    args.append("--no-device-info")
    args.append("--no-disc-mode")
    args.append("--no-cddb")
    args.append("--dvd")
    
    status, out, err = shared.launchSubProcess(args)

    # Output lines to list
    outAsList = out.splitlines()
   
    # Set up dictionary and list for storing track list and analysis report
    trackList = {}
    analysisReport = []
    
    # Locate track list and analysis report in cd-info output
    startIndexTrackList = shared.index_startswith_substring(outAsList, "CD-ROM Track List")
    startIndexAnalysisReport = shared.index_startswith_substring(outAsList, "CD Analysis Report")

    # Parse track list and store interesting bits in dictionary
    for i in range(startIndexTrackList + 2, startIndexAnalysisReport - 1, 1):
        thisTrack = outAsList[i]
        if thisTrack.startswith("++") == False:
            thisTrack = thisTrack.split(": ")
            trackNumber = int(thisTrack[0].strip())
            trackDetails = thisTrack[1].split()
            trackType = trackDetails[2]
            trackList[trackNumber] = trackType
        
    # Flags for presence of audio / data tracks
    containsAudio = "audio" in trackList.values()
    containsData = "data" in trackList.values()
        
    # Parse analysis report
    for i in range(startIndexAnalysisReport + 1, len(outAsList), 1):
        thisLine = outAsList[i]
        if thisLine.startswith("++") == False:
            analysisReport.append(thisLine)
    
    # Flags for CD/Extra / multisession / mixed-mode
    # Note that single-session mixed mode CDs are erroneously reported as
    # multisession by libcdio. See: http://savannah.gnu.org/bugs/?49090#comment1

    cdExtra = shared.index_startswith_substring(analysisReport, "CD-Plus/Extra") != -1
    multiSession = shared.index_startswith_substring(analysisReport, "session #") != -1
    mixedMode = shared.index_startswith_substring(analysisReport, "mixed mode CD") != -1

    # Main results to dictionary
    dictOut = {}
    dictOut["cdExtra"] = cdExtra
    dictOut["multiSession"] = multiSession
    dictOut["mixedMode"] = mixedMode
    dictOut["containsAudio"] = containsAudio
    dictOut["containsData"] = containsData
    dictOut["cd-info-status"] = status
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    
    return(dictOut)   
    
def main():

    # Configuration (move to config file later)
    
    cdDriveLetter = "I"
    cdInfoExe = "C:/cdio/cd-info.exe"
    prebatchExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Pre-Batch/Pre-Batch.exe"
    loadExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Load/Load.exe" 
    unloadExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Unload/Unload.exe"
    rejectExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Reject/Reject.exe"
    isoBusterExe = "C:/Program Files (x86)/Smart Projects/IsoBuster/IsoBuster.exe"
    cueRipperExe = "C:/CUETools/CUETools.ConsoleRipper.exe"
    shnToolExe = "C:/shntool/shntool.exe"
    tempDir = "C:/Temp/"
    # Following args to be given from command line
    batchFolder = "E:/nimbietest/"
    
    # Make configuration available to any module that imports 'config.py'
    config.cdDriveLetter = cdDriveLetter
    config.cdInfoExe = cdInfoExe
    config.prebatchExe = prebatchExe
    config.loadExe = loadExe
    config.unloadExe = unloadExe
    config.rejectExe = rejectExe
    config.isoBusterExe = isoBusterExe
    config.cueRipperExe = cueRipperExe
    config.shnToolExe = shnToolExe
    config.tempDir = tempDir
    config.batchFolder = batchFolder
        
    # Setup output terminal
    global out
    global err
       
    # Set encoding of the terminal to UTF-8
    if sys.version.startswith("2"):
        out = codecs.getwriter("UTF-8")(sys.stdout)
        err = codecs.getwriter("UTF-8")(sys.stderr)
    elif sys.version.startswith("3"):
        out = codecs.getwriter("UTF-8")(sys.stdout.buffer)
        err = codecs.getwriter("UTF-8")(sys.stderr.buffer)
    
    # Initialise batch
    resultPrebatch = drivers.prebatch()
    
    print("--- Starting load command")     
    # Load disc
    resultLoad = drivers.load()
    
    print(resultLoad)
    # Test if drive is ready for reading
    driveIsReady = False
    
    print("--- Entering  driveIsReady loop")
    
    # Exit after 10 s
    timeout = time.time() + 10
    while driveIsReady == False and time.time() < timeout:
        # TODO: define timeout value to prevent infinite loop in case of unreadable disc
        time.sleep(2)
        driveIsReady = testDrive(cdDriveLetter + ":")

    # Get disc info
    carrierInfo = getCarrierInfo()
    
    # Unload disc
    resultUnload = drivers.unload()
      
    print("====== Pre-batch =====================")
    #print(resultPrebatch)
    print("====== Load =====================")
    #print(resultLoad)
    print("====== carrierinfo =====================")
    print(carrierInfo)
    print("====== Unload =====================")
    #print(resultUnload)

    """
    discIndex = 0
    
    while True:
       # Load a new disc
       # Load.exe" --drive="I" --rejectifnodisc  --logfile="C:\Users\jkn010\AppData\Local\Temp\dBBC316.tmp"  --passerrorsback="C:\Users\jkn010\AppData\Local\Temp\dBBC317.tmp"
       loadArgs = "--drive=" + cdDriveLetter + " --rejectifnodisc  --logfile=" + batchFolder + "loadLog.txt" +  " --passerrorsback=" + batchFolder + "loadErr.txt" 
       loadStatus, loadOut, loadErr = launchSubProcess(loadExe + " " + loadArgs)
       
       # Detect disc type
       carrierInfo = getCarrierInfo(cdInfoExe, cdDriveLetter)
       print(carrierInfo)
       
       # Unload the disc
       # Unload.exe" --drive="I" --logfile="C:\Users\jkn010\AppData\Local\Temp\dBBC316.tmp"  --passerrorsback="C:\Users\jkn010\AppData\Local\Temp\dBBC317.tmp"
       unloadArgs = "--drive=" + cdDriveLetter + " --logfile=" + batchFolder + "unloadLog.txt" +  " --passerrorsback=" + batchFolder + "unloadErr.txt" 
       unloadStatus, unloadOut, unloadErr = launchSubProcess(unloadExe + " " + unloadArgs)
       
       discIndex += 1
       """
    
main()