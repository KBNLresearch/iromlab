import sys
import os
import isolyzer
import xml.etree.ElementTree as ETree
import config
import imp

def checkFileExists(fileIn):
    # Check if file exists and exit if not
    if os.path.isfile(fileIn) == False:
        msg = fileIn + " does not exist!"
        errorExit(msg)

def checkDirExists(dirIn):
    # Check if directory exists and exit if not
    if os.path.isdir(dirIn) == False:
        msg = dirIn + " does not exist!"
        errorExit(msg)
        
def errorExit(error):
    sys.stderr.write("Error - " + error + "\n")
    sys.exit()

def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
            or imp.is_frozen("__main__")) # tools/freeze
    
def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])

def findElementText(elt, elementPath):
    # Returns element text if it exists,
    # errorExit if it doesn't exist
    elementText = elt.findtext(elementPath)
    if elementText == None:
        msg = 'no element found at ' + elementPath
        errorExit(msg)
    else:
        return(elementText)
    
def getConfiguration():

    # Read configuration file, make all config variables available via
    # config.py and check that all file paths / executables exist.
    # This assumes an non-frozen script (no Py2Exe)

    # From where is this script executed?)
    rootPath = os.path.abspath(get_main_dir())
        
    # Configuration file
    configFile =  os.path.join(rootPath,'config.xml')

    # Check if config file exists and exit if not
    if os.path.isfile(configFile) == False:
        msg = 'configuration file not found'
        errorExit(msg)
    
    # Read contents to bytes object
    try:
        fConfig = open(configFile,"rb")
        configBytes = fConfig.read()
        fConfig.close()
    except IOError:
        msg = 'could not open configuration file'
        errorExit(msg)
     
    # Parse XML tree
    try:
        root = ETree.fromstring(configBytes)
    except Exception:
        msg = 'error parsing ' + configFile
        errorExit(msg)
    
    # Create empty element object & add config contents to it
    # A bit silly but allows use of findElementText in etpatch 
    
    configElt = ETree.Element("bogus")
    configElt.append(root)
    
    config.cdDriveLetter = findElementText(configElt, './config/cdDriveLetter')
    config.rootDir = findElementText(configElt, './config/rootDir')
    config.tempDir = findElementText(configElt, './config/tempDir')
    config.secondsToTimeout = findElementText(configElt, './config/secondsToTimeout')
    config.prebatchExe = findElementText(configElt, './config/prebatchExe')
    config.loadExe = findElementText(configElt, './config/loadExe')
    config.unloadExe = findElementText(configElt, './config/unloadExe')
    config.rejectExe = findElementText(configElt, './config/rejectExe')
    config.cdInfoExe = findElementText(configElt, './config/cdInfoExe')
    config.isoBusterExe = findElementText(configElt, './config/isoBusterExe')
    
    # Normalise all file paths
    config.rootDir = os.path.normpath(config.rootDir)
    config.tempDir = os.path.normpath(config.tempDir)
    config.prebatchExe = os.path.normpath(config.prebatchExe)
    config.loadExe = os.path.normpath(config.loadExe)
    config.unloadExe = os.path.normpath(config.unloadExe)
    config.rejectExe = os.path.normpath(config.rejectExe)
    config.cdInfoExe = os.path.normpath(config.cdInfoExe)
    config.isoBusterExe = os.path.normpath(config.isoBusterExe)
    
    # Check if all files and directories exist, and exit if not
    checkDirExists(config.rootDir)
    checkDirExists(config.tempDir)
    checkFileExists(config.prebatchExe)
    checkFileExists(config.loadExe)
    checkFileExists(config.unloadExe)
    checkFileExists(config.rejectExe)
    checkFileExists(config.cdInfoExe)
    checkFileExists(config.isoBusterExe)
    
def main():
    # Read configuration file
    getConfiguration()
    print(config.isoBusterExe)
    print(config.rootDir)
    print(config.secondsToTimeout)

main()
 
