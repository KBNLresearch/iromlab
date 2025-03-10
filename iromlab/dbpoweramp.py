#! /usr/bin/env python
"""Wrapper module for Isobuster"""

import os
import io
from . import config
from . import shared


def consoleRipper(writeDirectory):
    """Rip audio to to WAV or FLAC (depending on dBpoweramps settings in default profile)
    Uses the bespoke dBpoweramp console ripper which was developed at request of KB
    """

    # NOTE: logFile doesn't offer anything that's not in the secure extraction log
    # So it is simply discarded after ripping
    logFile = os.path.join(config.tempDir, shared.randomString(12) + ".log")
    secureExtractionLogFile = os.path.join(writeDirectory, "dbpoweramp.log")

    args = [config.dBpowerampConsoleRipExe]
    args.append("".join(["--drive=", config.cdDriveLetter]))
    args.append("".join(["--log=", logFile]))
    args.append("".join(["--path=", writeDirectory]))

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    status, out, err = shared.launchSubProcess(args)

    with io.open(logFile, "r", encoding="utf-8-sig") as fLog:
        log = fLog.read()
    fLog.close()

    # Remove log file
    os.remove(logFile)

    # Read Secure Extraction log and convert to UTF-8
    with io.open(secureExtractionLogFile, "r", encoding="utf-16") as fSecureExtractionLogFile:
        text = fSecureExtractionLogFile.read()
    fSecureExtractionLogFile.close()
    with io.open(secureExtractionLogFile, "w", encoding="utf-8") as fSecureExtractionLogFile:
        fSecureExtractionLogFile.write(text)
    fSecureExtractionLogFile.close()

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log

    return dictOut
