#! /usr/bin/env python

# Driver functions for Nimbie disc robot. These are all wrappers around
# the pre-batch, load, unload and reject utilities that are shipped with
# dBpoweramp

import os
import io
if __package__ == 'iromlab':
    from . import config
    from . import shared
else:
    import config
    import shared
    
def prebatch():
    logFile = os.path.join(config.tempDir,shared.randomString(12) + ".log")
    errorFile = os.path.join(config.tempDir,shared.randomString(12) + ".err")
    
    args = [config.prebatchExe]
    args.append("--drive=" + config.cdDriveLetter)
    args.append("--logfile=" + logFile)
    args.append("--passerrorsback=" + errorFile)
    
    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)
        
    status, out, err = shared.launchSubProcess(args)
    
    # Read log and error files. Encoding is little-Endian UTF-16
    with io.open(logFile, "r", encoding="utf-16le") as fLog:
        log = fLog.read()
    with io.open(errorFile, "r", encoding="utf-16le") as fErr:
        errors = fErr.read()   
       
    # Convert log and errors to UTF-8
    logUTF8 = log.encode('utf-8')
    errorsUTF8 = errors.encode('utf-8')
   
    os.remove(logFile)
    os.remove(errorFile)
 
    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = logUTF8
    dictOut["errors"] = errorsUTF8
    
    return(dictOut)
    
def load():
    logFile = os.path.join(config.tempDir,shared.randomString(12) + ".log")
    errorFile = os.path.join(config.tempDir,shared.randomString(12) + ".err")
    
    args = [config.loadExe]
    args.append("--drive=" + config.cdDriveLetter)
    args.append("--rejectifnodisc")
    args.append("--logfile=" + logFile)
    args.append("--passerrorsback=" + errorFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)
    
    status, out, err = shared.launchSubProcess(args)

    # Read log and error files. Encoding is little-Endian UTF-16
    with io.open(logFile, "r", encoding="utf-16le") as fLog:
        log = fLog.read()
    with io.open(errorFile, "r", encoding="utf-16le") as fErr:
        errors = fErr.read()   
       
    # Convert log and errors to UTF-8
    logUTF8 = log.encode('utf-8')
    errorsUTF8 = errors.encode('utf-8')
   
    os.remove(logFile)
    os.remove(errorFile)
         
    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = logUTF8
    dictOut["errors"] = errorsUTF8
    
    return(dictOut)

def unload():
    logFile = os.path.join(config.tempDir,shared.randomString(12) + ".log")
    errorFile = os.path.join(config.tempDir,shared.randomString(12) + ".err")
    
    args = [config.unloadExe]
    args.append("--drive=" + config.cdDriveLetter)
    args.append("--logfile=" + logFile)
    args.append("--passerrorsback=" + errorFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)
    
    status, out, err = shared.launchSubProcess(args)

    # Read log and error files. Encoding is little-Endian UTF-16
    with io.open(logFile, "r", encoding="utf-16le") as fLog:
        log = fLog.read()
    with io.open(errorFile, "r", encoding="utf-16le") as fErr:
        errors = fErr.read()   
       
    # Convert log and errors to UTF-8
    logUTF8 = log.encode('utf-8')
    errorsUTF8 = errors.encode('utf-8')
   
    os.remove(logFile)
    os.remove(errorFile)
     
    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = logUTF8
    dictOut["errors"] = errorsUTF8
    
    return(dictOut)

def reject():
    logFile = os.path.join(config.tempDir,shared.randomString(12) + ".log")
    errorFile = os.path.join(config.tempDir,shared.randomString(12) + ".err")
    
    args = [config.rejectExe]
    args.append("--drive=" + config.cdDriveLetter)
    args.append("--logfile=" + logFile)
    args.append("--passerrorsback=" + errorFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)
    
    status, out, err = shared.launchSubProcess(args)

    # Read log and error files. Encoding is little-Endian UTF-16
    with io.open(logFile, "r", encoding="utf-16le") as fLog:
        log = fLog.read()
    with io.open(errorFile, "r", encoding="utf-16le") as fErr:
        errors = fErr.read()   
       
    # Convert log and errors to UTF-8
    logUTF8 = log.encode('utf-8')
    errorsUTF8 = errors.encode('utf-8')
   
    os.remove(logFile)
    os.remove(errorFile)
     
    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = logUTF8
    dictOut["errors"] = errorsUTF8
    
    return(dictOut)
