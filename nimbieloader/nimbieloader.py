#! /usr/bin/env python
import sys
import os
import time
import imp
import glob
import codecs
import xml.etree.ElementTree as ETree
import config
import shared
import drivers
import win32api
import pprint
import hashlib
import logging

"""
Script for automated imaging / ripping of optical media using a Nimbie disc robot.

Features:

* Automated load / unload  / reject using dBpoweramp driver binaries
* Disc type detection using libcdio's cd-info tool
* Data CDs and DVDs are imaged to ISO file using IsoBuster
* Audio CDs are ripped to WAV using CueRipper (to be replaced with dBpoweramp later)  

Author: Johan van der Knijff
Research department,  KB / National Library of the Netherlands

"""

def errorExit(error, terminal):
    terminal.write("Error - " + error + "\n")
    sys.exit()

def testDrive(letter):
    """
    Tests a given drive letter to see if the drive is question is ready for 
    access. This is to handle things like floppy drives and USB card readers
    which have to have physical media inserted in order to be accessed.
    Returns true if the drive is ready, false if not.
    Source: http://stackoverflow.com/a/1020363
    """
    returnValue = False
    # This prevents Windows from showing an error to the user, and allows python 
    # to handle the exception on its own.
    oldError = win32api.SetErrorMode(1) #note that SEM_FAILCRITICALERRORS = 1
    try:
    	freeSpace = win32api.GetDiskFreeSpaceEx(letter)
    except:
    	returnValue = False
    else:
    	returnValue = True
    # restore the Windows error handling state to whatever it was before we
    # started messing with it:
    win32api.SetErrorMode(oldError)
    return(returnValue)
    
def getCarrierInfo():
    # Determine carrier type and number of sessions on carrier
    # cd-info command line:
    # cd-info -C d: --no-header --no-device-info --no-cddb --dvd
    
    args = [config.cdInfoExe]
    args.append( "-C")
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
    trackList = {}
    analysisReport = []
    
    # Locate track list and analysis report in cd-info output
    startIndexTrackList = shared.index_startswith_substring(outAsList, "CD-ROM Track List")
    startIndexAnalysisReport = shared.index_startswith_substring(outAsList, "CD Analysis Report")

    # Parse track list and store interesting bits in dictionary
    for i in range(startIndexTrackList + 2, startIndexAnalysisReport - 1, 1):
        thisTrack = outAsList[i]
        if thisTrack.startswith("++") == False:
            thisTrack = thisTrack.split(": ")
            trackNumber = int(thisTrack[0].strip())
            trackDetails = thisTrack[1].split()
            trackType = trackDetails[2]
            trackList[trackNumber] = trackType
        
    # Flags for presence of audio / data tracks
    containsAudio = "audio" in trackList.values()
    containsData = "data" in trackList.values()
        
    # Parse analysis report
    for i in range(startIndexAnalysisReport + 1, len(outAsList), 1):
        thisLine = outAsList[i]
        if thisLine.startswith("++") == False:
            analysisReport.append(thisLine)
    
    # Flags for CD/Extra / multisession / mixed-mode
    # Note that single-session mixed mode CDs are erroneously reported as
    # multisession by libcdio. See: http://savannah.gnu.org/bugs/?49090#comment1

    cdExtra = shared.index_startswith_substring(analysisReport, "CD-Plus/Extra") != -1
    multiSession = shared.index_startswith_substring(analysisReport, "session #") != -1
    mixedMode = shared.index_startswith_substring(analysisReport, "mixed mode CD") != -1

    # Main results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["cdExtra"] = cdExtra
    dictOut["multiSession"] = multiSession
    dictOut["mixedMode"] = mixedMode
    dictOut["containsAudio"] = containsAudio
    dictOut["containsData"] = containsData
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    
    return(dictOut)   

def isoBusterExtract(writeDirectory, session):
    # IsoBuster /d:i /ei:"E:\nimbieTest\myDiskIB.iso" /et:u /ep:oea /ep:npc /c /m /nosplash /s:1 /l:"E:\nimbieTest\ib.log"
    
    isoFile = os.path.join(writeDirectory, "disc.iso")
    logFile = ''.join([config.tempDir,shared.randomString(12),".log"])

    args = [config.isoBusterExe]
    args.append("".join(["/d:", config.cdDriveLetter, ":"]))
    args.append("".join(["/ei:", isoFile]))
    args.append("/et:u")
    args.append("/ep:oea")
    args.append("/ep:npc")
    args.append("/c")
    args.append("/m")
    args.append("/nosplash")
    args.append("".join(["/s:",str(session)]))
    args.append("".join(["/l:", logFile]))

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

def paranoiaRip(writeDirectory):

    logFile = ''.join([config.tempDir,shared.randomString(12),".log"])

    args = [config.cdParanoiaExe]
    args.append("-d")
    args.append("".join([config.cdDriveLetter, ":"]))
    args.append("-B")
    args.append("-l")
    args.append(logFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    # Not possible to define output path, so we have to temporarily
    # go to the write directory
    with shared.cd(writeDirectory):
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

def cdrdaoExtract(writeDirectory, session):
    # Extracts selected session to a single bin/toc file
    
    binFile = os.path.join(writeDirectory, "image.bin")
    tocFile = os.path.join(writeDirectory, "image.toc")

    args = [config.cdrdaoExe]
    args.append("read-cd")
    args.append("--read-raw")
    args.append("--device")
    args.append(config.cdDeviceName)
    args.append("--datafile")
    args.append(binFile)
    args.append("--driver")
    args.append("generic-mmc-raw")
    args.append("--session")
    args.append(str(session))
    args.append(tocFile)

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    # Not possible to define output path, so we have to temporarily
    # go to the write directory
    with shared.cd(writeDirectory):
        status, out, err = shared.launchSubProcess(args)
       
    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    
    return(dictOut)  

def generate_file_md5(fileIn):
    # Generate MD5 hash of file
    # fileIn is read in chunks to ensure it will work with (very) large files as well
    # Adapted from: http://stackoverflow.com/a/1131255/1209004

    blocksize = 2**20
    m = hashlib.md5()
    with open(fileIn, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()

def checksumDirectory(directory):
    # All files in directory
    allFiles = glob.glob(directory + "/*")
    
    # Dictionary for storing results
    checksums = {}
    
    for fName in allFiles:
        md5 = generate_file_md5(fName)
        checksums[fName] = md5
   
    # Write checksum file
    try:
        fChecksum = open(os.path.join(directory, "checksums.md5"), "w")
        for fName in checksums:
            lineOut = checksums[fName] + " " + os.path.basename(fName) + '\n'
            fChecksum.write(lineOut)
        fChecksum.close()
    except IOError:
        errorExit("Cannot write " + fChecksum, err)

def processDisc(id):
    
    logging.info(''.join(['### Disc identifier: ',id]))
        
    # Initialise reject status
    reject = False
            
    print("--- Starting load command")     
    # Load disc
    logging.info('*** Loading disc ***')
    resultLoad = drivers.load()
    logging.info(''.join(['load command: ', resultLoad['cmdStr']]))
    logging.info(''.join(['load command output: ',resultLoad['log'].strip()]))
    
    # Test if drive is ready for reading
    driveIsReady = False
    
    print("--- Entering  driveIsReady loop")
    
    # Reject if no CD is found after 20 s
    timeout = time.time() + 20
    while driveIsReady == False and time.time() < timeout:
        # TODO: define timeout value to prevent infinite loop in case of unreadable disc
        time.sleep(2)
        driveIsReady = testDrive(config.cdDriveLetter + ":")
    
    if driveIsReady == False:
        print("--- Entering  reject")
        resultReject = drivers.reject()
        logging.error('drive not ready')
        logging.info(''.join(['reject command: ', resultReject['cmdStr']]))
        logging.info(''.join(['reject command output: ',resultReject['log'].strip()]))
        #
        # !!IMPORTANT!!: we can end up here b/c of 2 situations:
        #
        # 1. No disc was loaded (b/c loader was empty at time 'load' command was run
        # 2. A disc was loaded, but it is not accessable (badly damaged disc)
        #
        # In production env. where ech disc corresponds to a catalog identifier in a
        # queue, 1. can simply be ignored (keep trying to load another disc, once disc
        # is loaded it can be linked to next catalog identifier in queue). However, in case
        # 2. the failed disc corresponds to the next identifier in the queue! So somehow
        # we need to distinguish these cases in order to keep discs in sync with identifiers!
        #
        # TODO: find out if case 2. is really possible (e.g. by using deliberately damaged/
        # unredable disc. If not, we can safely assume case 1. and adapt script accordingly.
        # 
        # RESULT: tested with blank CD, same behavior as no CD at all!
        # 
        # Possible solution: http://stackoverflow.com/a/2288126
    else:
        # Create output folder for this disc
        dirDisc = os.path.join(config.batchFolder, id)
        logging.info(''.join(['disc directory: ',dirDisc]))
    
        if not os.path.exists(dirDisc):
            os.makedirs(dirDisc)

        print("--- Entering  cd-info")
        # Get disc info
        logging.info('*** Running cd-info ***')
        carrierInfo = getCarrierInfo()
        logging.info(''.join(['cd-info command: ', carrierInfo['cmdStr']]))
        logging.info(''.join(['cd-info-status: ', str(carrierInfo['status'])]))
        logging.info(''.join(['cdExtra: ', str(carrierInfo['cdExtra'])]))
        logging.info(''.join(['containsAudio: ', str(carrierInfo['containsAudio'])]))
        logging.info(''.join(['containsData: ', str(carrierInfo['containsData'])]))
        logging.info(''.join(['mixedMode: ', str(carrierInfo['mixedMode'])]))
        logging.info(''.join(['multiSession: ', str(carrierInfo['multiSession'])]))
        
        # Assumptions in below workflow:
        # 1. Audio tracks are always part of 1st session
        # 2. If disc is of CD-Extra type, there's one data track on the 2nd session
        if carrierInfo["containsAudio"] == True:
            logging.info('*** Ripping audio ***')
            # Rip audio to WAV
            # TODO:
            # - dBpoweramp doesn't have command line interface
            # - CueRipper fails on Nimbie drive
            # - cdparanoia 10.2 (Windows) cannot extract audio from enhanced CDs
            # - cdrdao works, but only only produces bin/ toc files
            dirOut = os.path.join(dirDisc, "audio")
            if not os.path.exists(dirOut):
                os.makedirs(dirOut)
                
            resultCdrdao = cdrdaoExtract(dirOut, 1)
            logging.info(''.join(['cdrdao command: ', resultCdrdao['cmdStr']]))
            logging.info(''.join(['cdrdao-status: ', str(resultCdrdao['status'])]))
            # TODO: maybe include full cdrdao output?
            checksumDirectory(dirOut)
                        
            if carrierInfo["cdExtra"] == True and carrierInfo["containsData"] == True:
                logging.info('*** Extracting data session of cdExtra to ISO ***')
                print("--- Extract data session of cdExtra to ISO")
                # Create ISO file from data on 2nd session
                dirOut = os.path.join(dirDisc, "data")
                if not os.path.exists(dirOut):
                    os.makedirs(dirOut)
                
                resultIsoBuster = isoBusterExtract(dirOut, 2)
                checksumDirectory(dirOut)
                if resultIsoBuster["log"].strip() != "0":
                    reject = True
                    logging.error("Isobuster exited with error(s)")
                
                logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
                logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
                logging.info(''.join(['isobuster-log: ', resultIsoBuster['log'].strip()]))
                
        elif carrierInfo["containsData"] == True:
            logging.info('*** Extract data session to ISO ***')
            # Create ISO image of first session
            dirOut = os.path.join(dirDisc, "data")
            if not os.path.exists(dirOut):
                os.makedirs(dirOut)
                
            resultIsoBuster = isoBusterExtract(dirOut, 1)
            checksumDirectory(dirOut)
            if resultIsoBuster["log"].strip() != "0":
                reject = True
                logging.error("Isobuster exited with error(s)")
            
            logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
            logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
            logging.info(''.join(['isobuster-log: ', resultIsoBuster['log'].strip()]))

        print("--- Entering  unload")

        # Unload or reject disc
        if reject == False:
            logging.info('*** Unloading disc ***')
            resultUnload = drivers.unload()
            logging.info(''.join(['unload command: ', resultUnload['cmdStr']]))
            logging.info(''.join(['unload command output: ',resultUnload['log'].strip()]))
        else:
            logging.info('*** Rejecting disc ***')
            resultReject = drivers.reject()
            logging.info(''.join(['reject command: ', resultReject['cmdStr']]))
            logging.info(''.join(['reject command output: ', resultReject['log'].strip()]))

        
def main():

    # Configuration (move to config file later)
    
    cdDriveLetter = "I"
    cdDeviceName = "5,0,0" # only needed by cdrdao, remove later! 
    cdInfoExe = "C:/cdio/cd-info.exe"
    prebatchExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Pre-Batch/Pre-Batch.exe"
    loadExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Load/Load.exe" 
    unloadExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Unload/Unload.exe"
    rejectExe = "C:/Program Files/dBpoweramp/BatchRipper/Loaders/Nimbie/Reject/Reject.exe"
    isoBusterExe = "C:/Program Files (x86)/Smart Projects/IsoBuster/IsoBuster.exe"
    cueRipperExe = "C:/CUETools/CUETools.ConsoleRipper.exe"
    cdParanoiaExe = "C:/cdio/cd-paranoia.exe"
    cdrdaoExe = "C:/cdrdao/cdrdao.exe"
    shnToolExe = "C:/shntool/shntool.exe"
    tempDir = "C:/Temp/"
    # Following args to be given from command line
    batchFolder = "E:/nimbietest/"
    
    # Make configuration available to any module that imports 'config.py'
    config.cdDriveLetter = cdDriveLetter
    config.cdDeviceName = cdDeviceName
    config.cdInfoExe = cdInfoExe
    config.prebatchExe = prebatchExe
    config.loadExe = loadExe
    config.unloadExe = unloadExe
    config.rejectExe = rejectExe
    config.isoBusterExe = isoBusterExe
    config.cueRipperExe = cueRipperExe
    config.cdParanoiaExe = cdParanoiaExe
    config.cdrdaoExe = cdrdaoExe
    config.shnToolExe = shnToolExe
    config.tempDir = tempDir
    config.batchFolder = os.path.normpath(batchFolder)

    # Set up log file
    logFile = os.path.join(batchFolder, "batch.log")
    global logging
    logging.basicConfig(filename=logFile, 
                            level=logging.DEBUG, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Setup output terminal
    global out
    global err
       
    # Set encoding of the terminal to UTF-8
    if sys.version.startswith("2"):
        out = codecs.getwriter("UTF-8")(sys.stdout)
        err = codecs.getwriter("UTF-8")(sys.stderr)
    elif sys.version.startswith("3"):
        out = codecs.getwriter("UTF-8")(sys.stdout.buffer)
        err = codecs.getwriter("UTF-8")(sys.stderr.buffer)
            
    # Initialise batch
    logging.info('*** Initialising batch ***')
    resultPrebatch = drivers.prebatch()
    logging.info(''.join(['prebatch command: ', resultPrebatch['cmdStr']]))
    logging.info(''.join(['prebatch command output: ',resultPrebatch['log'].strip()]))
        
    # Internal identifier for this disc
    ids = ["001","002", "003"]
    for id in ids:
        # Process disc
        processDisc(id)

    
main()