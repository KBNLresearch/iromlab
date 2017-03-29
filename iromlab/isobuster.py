#! /usr/bin/env python

import os
import io

from isolyzer import isolyzer

if __package__ == 'iromlab':
    from . import config
    from . import shared
else:
    import config
    import shared
    
# Wrapper module for IsoBuster

def extractData(writeDirectory, session):
    # IsoBuster /d:i /ei:"E:\nimbieTest\myDiskIB.iso" /et:u /ep:oea /ep:npc /c /m /nosplash /s:1 /l:"E:\nimbieTest\ib.log"
    
    # Temporary name for ISO file; base name 
    isoFileTemp = os.path.join(writeDirectory, "disc.iso")
    #isoFile = os.path.join(writeDirectory, isoName)
    logFile = os.path.join(writeDirectory, "isobuster.log")

    args = [config.isoBusterExe]
    args.append("".join(["/d:", config.cdDriveLetter, ":"]))
    args.append("".join(["/ei:", isoFileTemp]))
    args.append("/et:u")
    args.append("/ep:oea")
    args.append("/ep:npc")
    args.append("/c")
    args.append("/m")
    args.append("/nosplash")
    args.append("".join(["/s:",str(session)]))
    args.append("".join(["/l:", logFile]))

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    status, out, err = shared.launchSubProcess(args)
    
    # Open and read log file
    with io.open(logFile, "r", encoding="cp1252") as fLog:
        log = fLog.read()
    fLog.close()

    # Rewrite as UTF-8
    with io.open(logFile, "w", encoding="utf-8") as fLog:
        fLog.write(log)
    fLog.close()
    
    # Run isolyzer ISO
    try:
        isolyzerResult = isolyzer.processImage(isoFileTemp)
        # Isolyzer status
        isolyzerSuccess = isolyzerResult.find('statusInfo/success').text       
        # Is ISO image smaller than expected (if True, this indicates the image may be truncated)
        imageTruncated = isolyzerResult.find('tests/smallerThanExpected').text               
        # Volume identifier from ISO's Primary Volume Descriptor 
        volumeIdentifier = isolyzerResult.find('properties/primaryVolumeDescriptor/volumeIdentifier').text.strip()
        if volumeIdentifier != '':
            # Rename ISO image using volumeIdentifier as a base name
            # Any spaces in volumeIdentifier are replaced with dashes 
            isoFile = os.path.join(writeDirectory, volumeIdentifier.replace(' ', '-') + '.iso')
            os.rename(isoFileTemp, isoFile)
            
    except IOError or AttributeError:
        volumeIdentifier = ''
        isolyzerSuccess = False
        imageTruncated = True
    
    # TODO: for added security we could also verify the ISO's MD5 against MD5 of physical disc. But this 
    # is slow + implementation under Windows will be ugly (with possible dependency on Cygwin because
    # not clear if Windows supports Unix-syle device paths)
    
    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log
    dictOut["volumeIdentifier"] = volumeIdentifier
    dictOut["isolyzerSuccess"] = isolyzerSuccess
    dictOut["imageTruncated"] = imageTruncated
        
    return(dictOut)
    
