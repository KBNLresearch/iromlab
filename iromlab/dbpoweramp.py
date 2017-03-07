#! /usr/bin/env python

import os
if __package__ == 'iromlab':
    from . import config
    from . import shared
else:
    import config
    import shared
    
# Wrapper module for dBpoweramp

def consoleRipper(writeDirectory):
    # Rip audio to to WAV or FLAC (depending on dBpoweramps settings in default profile)
    # Uses the bespoke dBpoweramp console ripper which was developed at request of KB 
    # dBpoweramp\kb-nl-consolerip.exe" --drive="D" --log=E:\cdBatchesTest\testconsolerip\log.txt --path=E:\cdBatchesTest\testconsolerip\
    #    

    logFile = os.path.join(config.tempDir,shared.randomString(12) + ".log")
       
    args = [config.dBpowerampConsoleRipExe]
    args.append("".join(["--drive=", config.cdDriveLetter]))
    args.append("".join(["--log=", logFile]))
    args.append("".join(["--path=", writeDirectory]))
  
    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)
        
    status, out, err = shared.launchSubProcess(args)
    
    # dBpoweramp writes UTF-8 BOM at start of file, open in binary mode and
    # then decode gets rid of the BOM
    fLog = open(logFile, 'rb')
    log = fLog.read().decode("utf-8-sig")
    fLog.close()
    os.remove(logFile)
        
    # Contents of log file to list
    logAsList = log.splitlines()
                
    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = logAsList
        
    return(dictOut)
