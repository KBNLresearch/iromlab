#! /usr/bin/env python
import sys
import os
import time
import imp
import glob
import codecs
import xml.etree.ElementTree as ETree
import sys
import subprocess as sub

def launchSubProcess(systemString):
    # Launch subprocess and return exit code, stdout and stderr
    try:
        # Execute command line; stdout + stderr redirected to objects
        # 'output' and 'errors'.
        p = sub.Popen(systemString,stdout=sub.PIPE,stderr=sub.PIPE, shell=True)
        output, errors = p.communicate()
                
        # Decode to UTF8
        outputAsString=output.decode('utf-8')
        errorsAsString=errors.decode('utf-8')
                
        exitStatus=p.returncode
  
    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus=-99
        outputAsString=""
        errorsAsString=""
    
    return(exitStatus,outputAsString,errorsAsString)

def index_startswith_substring(the_list, substring):
    for i, s in enumerate(the_list):
        if s.startswith(substring):
              return i
    return -1
    
def getCarrierInfo(cdInfoExe, cdDriveLetter):
    # Determine carrier type and number of sessions on carrier
    # cd-info command line:
    # cd-info -C d: --no-header --no-device-info --no-cddb --dvd
    
    cdInfoArgs = "-C " + cdDriveLetter + " --no-header --no-device-info --no-disc-mode --no-cddb --dvd"
    status, stdout, stderr = launchSubProcess(cdInfoExe + " " + cdInfoArgs)

    # Output lines to list
    outAsList = stdout.splitlines()
   
    # Set up dictionary and list for storing track list and analysis report
    trackList = {}
    analysisReport = []
    
    # Locate track list and analysis report in cd-info output
    startIndexTrackList = index_startswith_substring(outAsList, "CD-ROM Track List")
    startIndexAnalysisReport = index_startswith_substring(outAsList, "CD Analysis Report")

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

    cdExtra = "CD-Plus/Extra" in analysisReport
    multiSession = index_startswith_substring(analysisReport, "session #") != -1
    mixedMode = index_startswith_substring(analysisReport, "mixed mode CD") != -1

    # Main results to dictionary
    carrierInfo = {}
    carrierInfo["cdExtra"] = cdExtra
    carrierInfo["multiSession"] = multiSession
    carrierInfo["mixedMode"] = mixedMode
    carrierInfo["containsAudio"] = containsAudio
    carrierInfo["containsData"] = containsData
    carrierInfo["cd-info-status"] = status

    #print(trackList)
    
    return(carrierInfo)   
    
def main():
    # Configuration (move to config file later)
    cdDriveLetter = "I:"
    cdInfoExe = "C:/cdio/cd-info.exe"
    prebatchExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Pre-Batch/Pre-Batch.exe"
    loadExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Load/Load.exe" 
    unloadExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Unload/Unload.exe"
    rejectExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Reject/Reject.exe"
    isoBusterExe = "C:/Program Files (x86)/Smart Projects/IsoBuster/IsoBuster.exe"
    cueRipperExe = "C:/CUETools/CUETools.ConsoleRipper.exe"
    shnToolExe = "C:/shntool/shntool.exe"
    
    # Following args to be given from command line
    batchFolder = "E:/nimbietest/"
    
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
    prebatchArgs = "--drive=" + cdDriveLetter + " --logfile=" + batchFolder + "prebatchLog.txt" +  " --passerrorsback=" + batchFolder + "prebatchErr.txt"
    prebatchStatus, prebatchOut, prebatchErr = launchSubProcess(prebatchExe + " " + prebatchArgs)
    
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
    
main()