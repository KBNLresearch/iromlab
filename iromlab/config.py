#! /usr/bin/env python
"""Shared configuration constants"""

# Application
version = ""

# Disc Robot
driverScript  = ""
cdDriveLetter = ""
comPort       = "COM1" # default for Cronus
comSpeed      = "9600" # default for Cronus

reportFormatString = ""
cdInfoExe = ""
prebatchExe = ""
loadExe = ""
unloadExe = ""
rejectExe = ""
isoBusterExe = ""
dBpowerampConsoleRipExe = ""
shntoolExe = ""
flacExe = ""
tempDir = ""
rootDir = ""
batchFolder = ""
batchManifest = ""
jobsFolder = ""
secondsToTimeout = ""
prefixBatch = ""
audioFormat = ""
jobsFailedFolder = ""
socketHost = "127.0.0.1"
socketPort = "65432"
startOnFinalize = False
enablePPNLookup = True
enableSocketAPI = False
quitFlag = False
batchIsOpen = False
readyToStart = False
finishedBatch = False
