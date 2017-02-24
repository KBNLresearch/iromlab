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
    #logFile = ''.join([config.tempDir,shared.randomString(12),".log"])
    logFile = os.path.join(config.tempDir,shared.randomString(12) + ".log")

    args = [config.dBpowerampConsoleRipExe]
    args.append("".join(["--drive=", config.cdDriveLetter]))
    args.append("".join(["--log=", logFile]))
    args.append("".join(["--path=", writeDirectory]))
  
    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)
    
    ## TEST
    #print(cmdStr)
    ## TEST

    status, out, err = shared.launchSubProcess(args)

    ## TEST
    #print(str(status))
    #print(out)
    #print(err)
    ## TEST
    
    fLog = open(logFile, 'r')
    log = fLog.read()

    fLog.close()
    #os.remove(logFile)

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log
        
    return(dictOut)    

def main():
    config.tempDir = os.path.normpath("C:\Temp")
    config.dBpowerampConsoleRipExe = os.path.normpath("C:\Program Files\dBpoweramp\kb-nl-consolerip.exe")
    config.cdDriveLetter = "I"
    writeDirectory = os.path.normpath("E:\nimbieTest\kb-59b99052-fa98-11e6-9df7-00237d497a29\600dbdf0-fa98-11e6-aca1-00237d497a29")
    print(writeDirectory)
    
    test = consoleRipper(writeDirectory)
    #print(test)

if __name__ == "__main__":
    main()
    