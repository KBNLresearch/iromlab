#! /usr/bin/env python
"""Wrapper module for cd-info tool, provides information about optical drive and carriers"""

import os
import io
from . import config
from . import shared


def getCarrierInfo(writeDirectory):
    """Determine carrier type and number of sessions on carrier"""

    cdInfoLogFile = os.path.join(writeDirectory, "cd-info.log")

    args = [config.cdInfoExe]
    args.append("-C")
    args.append("".join([config.cdDriveLetter, ":"]))
    args.append("--no-header")
    args.append("--no-device-info")
    args.append("--no-disc-mode")
    args.append("--no-cddb")
    args.append("--dvd")

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    status, out, err = shared.launchSubProcess(args)

    # Output lines to list
    outAsList = out.splitlines()

    # Set up dictionary and list for storing track list and analysis report
    trackList = []
    analysisReport = []

    # Locate track list and analysis report in cd-info output
    startIndexTrackList = shared.index_startswith_substring(outAsList, "CD-ROM Track List")
    startIndexAnalysisReport = shared.index_startswith_substring(outAsList, "CD Analysis Report")

    # Parse track list and store interesting bits in dictionary
    for i in range(startIndexTrackList + 2, startIndexAnalysisReport - 1, 1):
        thisTrack = outAsList[i]
        if not thisTrack.startswith("++"):
            thisTrack = thisTrack.split(": ")
            trackNumber = int(thisTrack[0].strip())
            trackDetails = thisTrack[1].split()
            trackMSFStart = trackDetails[0]  # Minute:Second:Frame
            trackLSNStart = trackDetails[1]  # Logical Sector Number
            trackType = trackDetails[2]
            trackProperties = {}
            trackProperties['trackNumber'] = trackNumber
            trackProperties['trackMSFStart'] = trackMSFStart
            trackProperties['trackLSNStart'] = trackLSNStart
            trackProperties['trackType'] = trackType
            trackList.append(trackProperties)

    # Flags for presence of audio / data tracks
    containsAudio = False
    containsData = False
    dataTrackLSNStart = '0'

    for track in trackList:
        if track['trackType'] == 'audio':
            containsAudio = True
        if track['trackType'] == 'data':
            containsData = True
            dataTrackLSNStart = track['trackLSNStart']

    # Parse analysis report
    for i in range(startIndexAnalysisReport + 1, len(outAsList), 1):
        thisLine = outAsList[i]
        if not thisLine.startswith("++"):
            analysisReport.append(thisLine)

    # Flags for CD/Extra / multisession / mixed-mode
    # Note that single-session mixed mode CDs are erroneously reported as
    # multisession by libcdio. See: http://savannah.gnu.org/bugs/?49090#comment1

    cdExtra = shared.index_startswith_substring(analysisReport, "CD-Plus/Extra") != -1
    multiSession = shared.index_startswith_substring(analysisReport, "session #") != -1
    mixedMode = shared.index_startswith_substring(analysisReport, "mixed mode CD") != -1

    # Write cd-info output to log file
    with io.open(cdInfoLogFile, "w", encoding="utf-8") as fCdInfoLogFile:
        for line in outAsList:
            fCdInfoLogFile.write(line + "\n")
    fCdInfoLogFile.close()

    # Main results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["cdExtra"] = cdExtra
    dictOut["multiSession"] = multiSession
    dictOut["mixedMode"] = mixedMode
    dictOut["containsAudio"] = containsAudio
    dictOut["containsData"] = containsData
    dictOut["dataTrackLSNStart"] = dataTrackLSNStart
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err

    return dictOut


def getDrives():
    """Returns list of all optical drives"""

    args = [config.cdInfoExe]
    args.append("-l")

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    status, out, err = shared.launchSubProcess(args)

    # Output lines to list
    outAsList = out.splitlines()

    # Set up list for storing identified drives
    drives = []

    # Locate track list and analysis report in cd-info output
    startIndexDevicesList = shared.index_startswith_substring(outAsList, "list of devices found:")

    # Parse devices list and store Drive entries to list
    for i in range(startIndexDevicesList + 1, len(outAsList), 1):
        thisLine = outAsList[i]
        if thisLine.startswith("Drive"):
            thisDrive = thisLine.split("\\\\.\\")
            driveLetter = thisDrive[1].strip(":\n")
            drives.append(driveLetter)

    # Main results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["drives"] = drives
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err

    return dictOut
