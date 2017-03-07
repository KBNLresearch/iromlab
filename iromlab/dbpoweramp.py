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
    
    fLog = open(logFile, 'r')
    log = fLog.read()

    fLog.close()
    os.remove(logFile)
            
    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log
        
    return(dictOut)
