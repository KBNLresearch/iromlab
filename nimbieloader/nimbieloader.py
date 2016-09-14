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

def getCarrierInfo_cdrdao(cdrdaoExe, cdDriveLetter, cdDevicePath):
    # Determine carrier type and number of sessions on carrier
    # Obsolete, now superseded by cd-info based function below!
    
    cdrdaoArgs = "disk-info " + cdDevicePath
    cdrdaoStatus,cdrdaoOut,cdrdaoErrors = launchSubProcess(cdrdaoExe + " " + cdrdaoArgs)
    print("EXIT STATUS: " + str(cdrdaoStatus))
    
    carrierInfo = {}
    
    try:
        # Parse cdrdao output and store key-value pairs as a dictionary
        for line in cdrdaoOut.splitlines():
            thisRecord = line.split(":")
            key = thisRecord[0].strip()
            value = thisRecord[1].strip()
            carrierInfo[key] = value
    except:
        pass

    # Cdrdao output doesn't distiguish between audio and data CDs. Workaround:
    # look for .cda stub files (https://en.wikipedia.org/wiki/.cda_file). 
    # This only works under Windows!
    fileNames = [i for i in glob.glob(cdDriveLetter + "/*")]
    fileNamesCDA = [i for i in fileNames if i.endswith(".cda")]

    if len(fileNames) > 0 and len(fileNames) == len(fileNamesCDA):
        # Looks like an audio CD
        foundCdaStubFiles = True
    else:
        # Might still contain audio if this is a multisession CD!
        foundCdaStubFiles = False
    
    carrierInfo["foundCdaStubFiles"] = foundCdaStubFiles
    
    return(carrierInfo)

def getCarrierInfo(cdInfoExe, cdDriveLetter):
    # Determine carrier type and number of sessions on carrier
    
    # cd-info -C d: --no-header --no-device-info --no-cddb --dvd
    
    cdInfoArgs = "-C " + cdDriveLetter + " --no-header --no-device-info --no-cddb --dvd"
    status, stdout, stderr = launchSubProcess(cdInfoExe + " " + cdInfoArgs)
    print("EXIT STATUS: " + str(status))
    print(stdout)
    
    carrierInfo = {}
    
    """
    try:
        # Parse cdrdao output and store key-value pairs as a dictionary
        for line in cdrdaoOut.splitlines():
            thisRecord = line.split(":")
            key = thisRecord[0].strip()
            value = thisRecord[1].strip()
            carrierInfo[key] = value
    except:
        pass
    """
    return(carrierInfo)   
    
    
def main():
    # Configuration (move to config file later)
    cdDriveLetter = "D:"
    cdDevicePath = "0,0,0"
    cdrdaoExe = "C:/cdrdao/cdrdao.exe"
    cdInfoExe = "C:/cdio/cd-info.exe"
    prebatchExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Pre-Batch/Pre-Batch.exe"
    loadExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Load/Load.exe" 
    unloadExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Unload/Unload.exe"
    rejectExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Reject/Reject.exe"
    isoBusterExe = "C:/Program Files (x86)/Smart Projects/IsoBuster/IsoBuster.exe"

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
    
    # Get carrier info
    #carrierInfo = getCarrierInfo(cdrdaoExe, cdDriveLetter, cdDevicePath)
    carrierInfo = getCarrierInfo(cdInfoExe, cdDriveLetter)
    print(carrierInfo)
    
main()