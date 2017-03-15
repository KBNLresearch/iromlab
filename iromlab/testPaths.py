#! /usr/bin/env python

import os
import xml.etree.ElementTree as ETree
import config

def errorExit(msg):
    msgString=("Error: " + msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()

def findElementText(elt, elementPath):
    # Returns element text if it exists,
    # errorExit if it doesn't exist
    elementText = elt.findtext(elementPath)
    if elementText == None:
        msg = 'no element found at ' + elementPath
        errorExit(msg)
    else:
        return(elementText)
    
def main():

    configFileUser = os.path.normpath('E:/crap/config.xml')

    # Check if user config file exists and exit if not
    if os.path.isfile(configFileUser) == False:
        msg = 'configuration file not found'
        errorExit(msg)
    
    # Read contents to bytes object
    try:
        fConfig = open(configFileUser,"rb")
        configBytes = fConfig.read()
        fConfig.close()
    except IOError:
        msg = 'could not open configuration file'
        errorExit(msg)
     
    # Parse XML tree
    try:
        root = ETree.fromstring(configBytes)
    except Exception:
        msg = 'error parsing ' + configFileUser
        errorExit(msg)
    
    # Create empty element object & add config contents to it
    # A bit silly but allows use of findElementText in etpatch 
    
    configElt = ETree.Element("bogus")
    configElt.append(root)
    
    config.cdDriveLetter = findElementText(configElt, './config/cdDriveLetter')
    config.rootDir = findElementText(configElt, './config/rootDir')
    print(config.rootDir)
    #tempDir = findElementText(configElt, './config/tempDir')
    #secondsToTimeout = findElementText(configElt, './config/secondsToTimeout')
    #prefixBatch = findElementText(configElt, './config/prefixBatch')
    #audioFormat = findElementText(configElt, './config/audioFormat')
    #prebatchExe = findElementText(configElt, './config/prebatchExe')
    #loadExe = findElementText(configElt, './config/loadExe')
    #unloadExe = findElementText(configElt, './config/unloadExe')
    #rejectExe = findElementText(configElt, './config/rejectExe')
    #isoBusterExe = findElementText(configElt, './config/isoBusterExe')
    #dBpowerampConsoleRipExe = findElementText(configElt, './config/dBpowerampConsoleRipExe')
    
    # Normalise all file paths
    config.rootDir = os.path.normpath(config.rootDir)
    print(config.rootDir)
    #tempDir = os.path.normpath(tempDir)
    #prebatchExe = os.path.normpath(prebatchExe)
    #loadExe = os.path.normpath(loadExe)
    #unloadExe = os.path.normpath(unloadExe)
    #rejectExe = os.path.normpath(rejectExe)
    #isoBusterExe = os.path.normpath(isoBusterExe)
    #dBpowerampConsoleRipExe = os.path.normpath(dBpowerampConsoleRipExe)
        
    print(config.rootDir)
    
    batchID = '\test'
    jobID = '012347'
    batchFolder = os.path.join(config.rootDir, batchID)
    
    dirDisc = os.path.join(batchFolder, jobID)
    print(dirDisc)
    
    test = 'D:\testfolder'
    print(test)
    

main()