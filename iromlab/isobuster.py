#! /usr/bin/env python
"""Wrapper module for Isobuster"""

import os
import io
from isolyzer import isolyzer
from . import config
from . import shared


def extractData(writeDirectory, session, dataTrackLSNStart):
    """Extract data to ISO image using specified session number"""

    # Temporary name for ISO file; base name
    isoFileTemp = os.path.join(writeDirectory, "disc.iso")
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
    args.append("".join(["/s:", str(session)]))
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

    # Run isolyzer to verify if ISO is complete and extract volume identifier text string
    try:
        isolyzerResult = isolyzer.processImage(isoFileTemp, dataTrackLSNStart)
        # Isolyzer status
        isolyzerSuccess = isolyzerResult.find('statusInfo/success').text
        # Is ISO image smaller than expected (if True, this indicates the image may be truncated)
        imageTruncated = isolyzerResult.find('tests/smallerThanExpected').text
        # Volume identifier from ISO's Primary Volume Descriptor
        # TODO: make this work for other fs types as well (UDF, HFS, HFS+)
        volumeIdentifier = isolyzerResult.find("fileSystems/fileSystem[@TYPE='ISO 9660']"
                                               "/primaryVolumeDescriptor/"
                                               "volumeIdentifier").text.strip()

    except IOError or AttributeError:
        volumeIdentifier = ''
        isolyzerSuccess = False
        imageTruncated = True

    if volumeIdentifier != '':
        # Rename ISO image using volumeIdentifier as a base name
        # Any spaces in volumeIdentifier are replaced with dashes
        isoFile = os.path.join(writeDirectory, volumeIdentifier.replace(' ', '-') + '.iso')
        os.rename(isoFileTemp, isoFile)

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

    return dictOut
