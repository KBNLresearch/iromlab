#! /usr/bin/env python

# Driver functions for Nimbie disc robot. These are all wrappers around
# the pre-batch, load, unload and reject utilities that are shipped with
# dBpoweramp

import os
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
    fLog = open(logFile, 'r')
    fErr = open(errorFile, 'r')
    log = fLog.read()
    errors = fErr.read()
    
    # Convert log and errors from little-Endian UTF-16 to UTF-8
    logUTF8 = log.encode('utf-8').decode('utf-16le')
    errorsUTF8 = errors.encode('utf-8').decode('utf-16le')
    
    fLog.close()
    fErr.close()
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
    fLog = open(logFile, 'r')
    fErr = open(errorFile, 'r')
    log = fLog.read()
    errors = fErr.read()
    
    # Convert log and errors from little-Endian UTF-16 to UTF-8
    logUTF8 = log.encode('utf-8').decode('utf-16le')
    errorsUTF8 = errors.encode('utf-8').decode('utf-16le')
    
    fLog.close()
    fErr.close()
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
    fLog = open(logFile, 'r')
    fErr = open(errorFile, 'r')
    log = fLog.read()
    errors = fErr.read()
    
    # Convert log and errors from little-Endian UTF-16 to UTF-8
    logUTF8 = log.encode('utf-8').decode('utf-16le')
    errorsUTF8 = errors.encode('utf-8').decode('utf-16le')
    
    fLog.close()
    fErr.close()
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
    fLog = open(logFile, 'r')
    fErr = open(errorFile, 'r')
    log = fLog.read()
    errors = fErr.read()
    
    # Convert log and errors from little-Endian UTF-16 to UTF-8
    logUTF8 = log.encode('utf-8').decode('utf-16le')
    errorsUTF8 = errors.encode('utf-8').decode('utf-16le')
    
    fLog.close()
    fErr.close()
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
