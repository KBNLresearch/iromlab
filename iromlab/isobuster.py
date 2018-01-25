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
    reportFile = os.path.join(writeDirectory, "isobuster-report.xml")
    
    # Format string that defines DFXML output report
    reportFormatString = config.reportFormatString

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
    args.append("".join(["/tree:all:", reportFile, '?', reportFormatString]))

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
        try:
            isolyzerSuccess = isolyzerResult.find('statusInfo/success').text
        except AttributeError:
            isolyzerSuccess = False

        # Is ISO image smaller than expected (if True, this indicates the image may be truncated)
        try:
            imageTruncated = isolyzerResult.find('tests/smallerThanExpected').text
        except AttributeError:
            imageTruncated = True

        # Volume identifier from ISO's Primary Volume Descriptor
        try:
            volumeIdentifier = isolyzerResult.find("fileSystems/fileSystem[@TYPE='ISO 9660']"
                                               "/primaryVolumeDescriptor/"
                                               "volumeIdentifier").text.strip()
        except AttributeError:
            volumeIdentifier = ''

        # Logical Volume identifier from UDF Logical Volume Descriptor
        # NOTE: beware of possible encoding issues due to use of "OSTA compressed
        # Unicode", the meaning of which is not entirely clear to me!
        try:
            logicalVolumeIdentifier = isolyzerResult.find("fileSystems/fileSystem[@TYPE='UDF']"
                                               "/logicalVolumeDescriptor/"
                                               "logicalVolumeIdentifier").text.strip()
        except AttributeError:
            logicalVolumeIdentifier = ''

        # Volume Name from HFS Master Directory Block
        try:
            volumeName = isolyzerResult.find("fileSystems/fileSystem[@TYPE='HFS']"
                                               "/masterDirectoryBlock/"
                                               "volumeName").text.strip()
        except AttributeError:
            volumeName = ''

        if volumeIdentifier != '':
            volumeLabel = volumeIdentifier
        elif volumeIdentifier == '' and logicalVolumeIdentifier != '':
            volumeLabel = logicalVolumeIdentifier
        elif volumeIdentifier == '' and volumeName != '':
            volumeLabel = volumeName
        else:
            volumeLabel = ''

    except IOError:
        volumeLabel = ''
        isolyzerSuccess = False
        imageTruncated = True

    if volumeLabel != '':
        # Rename ISO image using volumeLabel as a base name
        # Any spaces in volumeLabel are replaced with dashes
        isoFile = os.path.join(writeDirectory, volumeLabel.replace(' ', '-') + '.iso')
        os.rename(isoFileTemp, isoFile)

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log
    dictOut["volumeIdentifier"] = volumeLabel
    dictOut["isolyzerSuccess"] = isolyzerSuccess
    dictOut["imageTruncated"] = imageTruncated

    return dictOut
