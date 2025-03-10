#! /usr/bin/env python
"""This module contains iromlab's cdWorker code, i.e. the code that monitors
the list of jobs (submitted from the GUI) and does the actual imaging and ripping
"""

import sys
import os
import shutil
import time
import glob
import csv
import hashlib
import logging
import pythoncom
import wmi
import _thread as thread
from . import config
from . import drivers
from . import cdinfo
from . import isobuster
from . import dbpoweramp
from . import verifyaudio
from . import mdo

def mediumLoaded(driveName):
    """Returns True if medium is loaded (also if blank/unredable), False if not"""

    # Use CoInitialize to avoid errors like this:
    # http://stackoverflow.com/questions/14428707/python-function-is-unable-to-run-in-new-thread
    pythoncom.CoInitialize()
    c = wmi.WMI()
    foundDriveName = False
    loaded = False
    for cdrom in c.Win32_CDROMDrive():
        if cdrom.Drive == driveName:
            foundDriveName = True
            loaded = cdrom.MediaLoaded

    return(foundDriveName, loaded)


def generate_file_md5(fileIn):
    """Generate MD5 hash of file"""

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


def generate_file_sha512(fileIn):
    """Generate sha512 hash of file"""

    # fileIn is read in chunks to ensure it will work with (very) large files as well
    # Adapted from: http://stackoverflow.com/a/1131255/1209004

    blocksize = 2**20
    m = hashlib.sha512()
    with open(fileIn, "rb") as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update(buf)
    return m.hexdigest()


def checksumDirectory(directory):
    """Calculate checksums for all files in directory"""

    # All files in directory
    allFiles = glob.glob(directory + "/*")

    # Dictionary for storing results
    checksums = {}

    for fName in allFiles:
        hashString = generate_file_sha512(fName)
        checksums[fName] = hashString

    # Write checksum file
    try:
        fChecksum = open(os.path.join(directory, "checksums.sha512"), "w", encoding="utf-8")
        for fName in checksums:
            lineOut = checksums[fName] + " " + os.path.basename(fName) + '\n'
            fChecksum.write(lineOut)
        fChecksum.close()
        wroteChecksums = True
    except IOError:
        wroteChecksums = False

    return wroteChecksums


def processDisc(carrierData):
    """Process one disc / job"""

    jobID = carrierData['jobID']
    PPN = carrierData['PPN']

    logging.info(''.join(['### Job identifier: ', jobID]))
    logging.info(''.join(['PPN: ', carrierData['PPN']]))
    logging.info(''.join(['Title: ', carrierData['title']]))
    logging.info(''.join(['Volume number: ', carrierData['volumeNo']]))

    # Initialise reject and success status
    reject = False
    success = True

    # Create output folder for this disc
    dirDisc = os.path.join(config.batchFolder, jobID)
    logging.info(''.join(['disc directory: ', dirDisc]))
    if not os.path.exists(dirDisc):
        os.makedirs(dirDisc)

    # Load disc
    logging.info('*** Loading disc ***')
    resultLoad = drivers.load()
    logging.info(''.join(['load command: ', resultLoad['cmdStr']]))
    logging.info(''.join(['load command output: ', resultLoad['log'].strip()]))

    # Test if disc is loaded
    discLoaded = False

    # Reject if no CD is found after 20 s
    timeout = time.time() + int(config.secondsToTimeout)
    while not discLoaded and time.time() < timeout:
        # Timeout value prevents infinite loop in case of unreadable disc
        time.sleep(2)
        foundDrive, discLoaded = mediumLoaded(config.cdDriveLetter + ":")

    if not foundDrive:
        success = False
        logging.error(''.join(['drive ', config.cdDriveLetter, ' does not exist']))

    if not discLoaded:
        success = False
        resultReject = drivers.reject()
        logging.error('no disc loaded')
        logging.info(''.join(['reject command: ', resultReject['cmdStr']]))
        logging.info(''.join(['reject command output: ', resultReject['log'].strip()]))
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
        # UPDATE: Case 1. can be eliminated if loading of a CD is made dependent of
        # a queue of disc ids (which are entered by operator at time of adding a CD)
        #
        # In that case:
        #
        # queue is empty --> no CD in loader --> pause loading until new item in queue
        #
        # (Can still go wrong if items are entered in queue w/o loading any CDs, but
        # this is an edge case)

        # Create dummy carrierInfo dictionary (values are needed for batch manifest)
        carrierInfo = {}
        carrierInfo['containsAudio'] = False
        carrierInfo['containsData'] = False
        carrierInfo['cdExtra'] = False
        carrierInfo['mixedMode'] = False
        carrierInfo['cdInteractive'] = False
    else:
        # Get disc info
        logging.info('*** Running cd-info ***')
        carrierInfo = cdinfo.getCarrierInfo(dirDisc)
        logging.info(''.join(['cd-info command: ', carrierInfo['cmdStr']]))
        logging.info(''.join(['cd-info-status: ', str(carrierInfo['status'])]))
        logging.info(''.join(['cdExtra: ', str(carrierInfo['cdExtra'])]))
        logging.info(''.join(['containsAudio: ', str(carrierInfo['containsAudio'])]))
        logging.info(''.join(['containsData: ', str(carrierInfo['containsData'])]))
        logging.info(''.join(['mixedMode: ', str(carrierInfo['mixedMode'])]))
        logging.info(''.join(['cdInteractive: ', str(carrierInfo['cdInteractive'])]))
        logging.info(''.join(['multiSession: ', str(carrierInfo['multiSession'])]))

        # Assumptions in below workflow:
        # 1. Audio tracks are always part of 1st session
        # 2. If disc is of CD-Extra type, there's one data track on the 2nd session
        if carrierInfo["containsAudio"]:
            logging.info('*** Ripping audio ***')
            # Rip audio using dBpoweramp console ripper
            resultdBpoweramp = dbpoweramp.consoleRipper(dirDisc)
            statusdBpoweramp = str(resultdBpoweramp["status"])
            logdBpoweramp = resultdBpoweramp["log"]
            # secureExtractionLog = resultdBpoweramp["secureExtractionLog"]

            if statusdBpoweramp != "0":
                success = False
                reject = True
                logging.error("dBpoweramp exited with error(s)")

            logging.info(''.join(['dBpoweramp command: ', resultdBpoweramp['cmdStr']]))
            logging.info(''.join(['dBpoweramp-status: ', str(resultdBpoweramp['status'])]))
            logging.info("dBpoweramp log:\n" + logdBpoweramp)

            # Verify that created audio files are not corrupt (using shntool / flac)
            logging.info('*** Verifying audio ***')
            audioHasErrors, audioErrorsList = verifyaudio.verifyCD(dirDisc, config.audioFormat)
            logging.info(''.join(['audioHasErrors: ', str(audioHasErrors)]))

            if audioHasErrors:
                success = False
                reject = True
                logging.error("Verification of audio files resulted in error(s)")

            # TODO perhaps indent this block if we only want this in case of actual errors?
            logging.info("Output of audio verification:")
            for audioFile in audioErrorsList:
                for item in audioFile:
                    logging.info(item)

            if carrierInfo["containsData"]:
                if carrierInfo["cdExtra"]:
                    logging.info('*** Extracting data session of cdExtra to ISO ***')
                    # Create ISO file from data on 2nd session
                    dataTrackLSNStart = int(carrierInfo['dataTrackLSNStart'])
                    resultIsoBuster = isobuster.extractData(dirDisc, 2, dataTrackLSNStart)
                elif carrierInfo["mixedMode"]:
                    logging.info('*** Extracting data session of mixedMode disc to ISO ***')
                    dataTrackLSNStart = int(carrierInfo['dataTrackLSNStart'])
                    resultIsoBuster = isobuster.extractData(dirDisc, 1, dataTrackLSNStart)

                statusIsoBuster = resultIsoBuster["log"].strip()
                isolyzerSuccess = resultIsoBuster['isolyzerSuccess']
                imageTruncated = resultIsoBuster['imageTruncated']

                if statusIsoBuster != "0":
                    success = False
                    reject = True
                    logging.error("Isobuster exited with error(s)")

                elif not isolyzerSuccess:
                    success = False
                    reject = True
                    logging.error("Isolyzer exited with error(s)")

                elif imageTruncated:
                    success = False
                    reject = True
                    logging.error("Isolyzer detected truncated ISO image")

                logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
                logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
                logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
                logging.info(''.join(['volumeIdentifier: ',
                                      str(resultIsoBuster['volumeIdentifier'])]))
                logging.info(''.join(['isolyzerSuccess: ', str(isolyzerSuccess)]))
                logging.info(''.join(['imageTruncated: ', str(imageTruncated)]))

        elif carrierInfo["containsData"] and not carrierInfo["cdInteractive"]:
            logging.info('*** Extracting data session to ISO ***')
            # Create ISO image of first session
            resultIsoBuster = isobuster.extractData(dirDisc, 1, 0)

            statusIsoBuster = resultIsoBuster["log"].strip()
            isolyzerSuccess = resultIsoBuster['isolyzerSuccess']
            imageTruncated = resultIsoBuster['imageTruncated']

            if statusIsoBuster != "0":
                success = False
                reject = True
                logging.error("Isobuster exited with error(s)")

            elif not isolyzerSuccess:
                success = False
                reject = True
                logging.error("Isolyzer exited with error(s)")

            elif imageTruncated:
                success = False
                reject = True
                logging.error("Isolyzer detected truncated ISO image")

            logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
            logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
            logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
            logging.info(''.join(['volumeIdentifier: ', str(resultIsoBuster['volumeIdentifier'])]))
            logging.info(''.join(['isolyzerSuccess: ', str(isolyzerSuccess)]))
            logging.info(''.join(['imageTruncated: ', str(imageTruncated)]))

        elif carrierInfo["cdInteractive"]:
            logging.info('*** Extracting data from CD Interactive to raw image file ***')
            resultIsoBuster = isobuster.extractCdiData(dirDisc)
            statusIsoBuster = resultIsoBuster["log"].strip()

            if statusIsoBuster != "0":
                success = False
                reject = True
                logging.error("Isobuster exited with error(s)")

            logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
            logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
            logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
        
        else:
            # We end up here if cd-info wasn't able to identify the disc
            success = False
            reject = True
            logging.error("Unable to identify disc type")

        if config.enablePPNLookup:
            # Fetch metadata from KBMDO and store as file
            logging.info('*** Writing metadata from KB-MDO to file ***')

            successMdoWrite = mdo.writeMDORecord(PPN, dirDisc)
            if not successMdoWrite:
                success = False
                reject = True
                logging.error("Could not write metadata from KB-MDO")

        # Generate checksum file
        logging.info('*** Computing checksums ***')
        successChecksum = checksumDirectory(dirDisc)

        if not successChecksum:
            success = False
            reject = True
            logging.error("Writing of checksum file resulted in an error")

        # Unload or reject disc
        if not reject:
            logging.info('*** Unloading disc ***')
            resultUnload = drivers.unload()
            logging.info(''.join(['unload command: ', resultUnload['cmdStr']]))
            logging.info(''.join(['unload command output: ', resultUnload['log'].strip()]))
        else:
            logging.info('*** Rejecting disc ***')
            resultReject = drivers.reject()
            logging.info(''.join(['reject command: ', resultReject['cmdStr']]))
            logging.info(''.join(['reject command output: ', resultReject['log'].strip()]))

    # Create comma-delimited batch manifest entry for this carrier

    # VolumeIdentifier only defined for ISOs, not for pure audio CDs and CD Interactive!
    if discLoaded and carrierInfo["containsData"]:
        try:
            volumeID = resultIsoBuster['volumeIdentifier'].strip()
        except Exception:
            volumeID = ''
    else:
        volumeID = ''

    # Put all items for batch manifest entry in a list
    rowBatchManifest = ([jobID,
                         carrierData['PPN'],
                         carrierData['volumeNo'],
                         carrierData['title'],
                         volumeID,
                         str(success),
                         str(carrierInfo['containsAudio']),
                         str(carrierInfo['containsData']),
                         str(carrierInfo['cdExtra']),
                         str(carrierInfo['mixedMode']),
                         str(carrierInfo['cdInteractive'])])

    # Open batch manifest in append mode
    bm = open(config.batchManifest, "a", encoding="utf-8")

    # Create CSV writer object
    csvBm = csv.writer(bm, lineterminator='\n')

    # Write row to batch manifest and close file
    csvBm.writerow(rowBatchManifest)
    bm.close()
    return success


def processDiscTest(carrierData):
    """Dummy version of processDisc function that doesn't do any actual imaging
    used for testing only
    """
    jobID = carrierData['jobID']
    logging.info(''.join(['### Job identifier: ', jobID]))
    logging.info(''.join(['PPN: ', carrierData['PPN']]))
    logging.info(''.join(['Title: ', carrierData['title']]))
    logging.info(''.join(['Volume number: ', carrierData['volumeNo']]))

    # Create dummy carrierInfo dictionary (values are needed for batch manifest)
    carrierInfo = {}
    carrierInfo['containsAudio'] = False
    carrierInfo['containsData'] = False
    carrierInfo['cdExtra'] = False

    success = True

    # Create comma-delimited batch manifest entry for this carrier

    # Dummy value for VolumeIdentifier
    volumeID = 'DUMMY'

    # Put all items for batch manifest entry in a list

    rowBatchManifest = ([jobID,
                         carrierData['PPN'],
                         carrierData['volumeNo'],
                         carrierData['title'],
                         volumeID,
                         str(success),
                         str(carrierInfo['containsAudio']),
                         str(carrierInfo['containsData']),
                         str(carrierInfo['cdExtra'])])

    # Open batch manifest in append mode
    bm = open(config.batchManifest, "a", encoding="utf-8")

    # Create CSV writer object
    csvBm = csv.writer(bm, lineterminator='\n')

    # Write row to batch manifest and close file
    csvBm.writerow(rowBatchManifest)
    bm.close()

    return success


def quitIromlab():
    """Send KeyboardInterrupt after user pressed Exit button"""
    logging.info('*** Quitting because user pressed Exit ***')
    # Wait 2 seconds to avoid race condition between logging and KeyboardInterrupt
    time.sleep(2)
    # This triggers a KeyboardInterrupt in the main thread
    thread.interrupt_main()


def cdWorker():
    """Worker function that monitors the job queue and processes the discs in FIFO order"""

    # Initialise 'success' flag to prevent run-time error in case user
    # finalizes batch before entering any carriers (edge case)
    success = True

    # Loop periodically scans value of config.batchFolder
    while not config.readyToStart:
        time.sleep(2)

    # Write Iromlab version to file in batch
    versionFile = os.path.join(config.batchFolder, 'version.txt')
    with open(versionFile, "w") as vf:
        vf.write(config.version + '\n')

    # Define batch manifest (CSV file with minimal metadata on each carrier)
    config.batchManifest = os.path.join(config.batchFolder, 'manifest.csv')

    # Write header row if batch manifest doesn't exist already
    if not os.path.isfile(config.batchManifest):
        headerBatchManifest = (['jobID',
                                'PPN',
                                'volumeNo',
                                'title',
                                'volumeID',
                                'success',
                                'containsAudio',
                                'containsData',
                                'cdExtra',
                                'mixedMode',
                                'cdInteractive'])

        # Open batch manifest in append mode
        bm = open(config.batchManifest, "a", encoding="utf-8")

        # Create CSV writer object
        csvBm = csv.writer(bm, lineterminator='\n')

        # Write header to batch manifest and close file
        csvBm.writerow(headerBatchManifest)
        bm.close()

    # Initialise batch
    logging.info('*** Initialising batch ***')
    resultPrebatch = drivers.prebatch()
    logging.info(''.join(['prebatch command: ', resultPrebatch['cmdStr']]))
    logging.info(''.join(['prebatch command output: ', resultPrebatch['log'].strip()]))

    # Flag that marks end of batch (main processing loop keeps running while False)
    endOfBatchFlag = False

    # Check if user pressed Exit, and quit if so ...
    if config.quitFlag:
        quitIromlab()

    while not endOfBatchFlag and not config.quitFlag:
        time.sleep(2)

        # Get directory listing, sorted by creation time
        # List conversion because in Py3 a filter object is not a list!
        files = list(filter(os.path.isfile, glob.glob(config.jobsFolder + '/*')))
        files.sort(key=lambda x: os.path.getctime(x))

        noFiles = len(files)

        if noFiles > 0:
            # Identify oldest job file
            jobOldest = files[0]

            # Open job file and read contents
            fj = open(jobOldest, "r", encoding="utf-8")

            fjCSV = csv.reader(fj)
            jobList = next(fjCSV)
            fj.close()

            if jobList[0] == 'EOB':
                # End of current batch
                endOfBatchFlag = True
                config.readyToStart = False
                config.finishedBatch = True
                config.batchIsOpen = False
                os.remove(jobOldest)
                shutil.rmtree(config.jobsFolder)
                shutil.rmtree(config.jobsFailedFolder)
                logging.info('*** End Of Batch job found, closing batch ***')
                # Wait 2 seconds to avoid race condition between logging and KeyboardInterrupt
                time.sleep(2)
                # This triggers a KeyboardInterrupt in the main thread
                thread.interrupt_main()
            else:
                # Set up dictionary that holds carrier data
                carrierData = {}
                carrierData['jobID'] = jobList[0]
                carrierData['PPN'] = jobList[1]
                carrierData['title'] = jobList[2]
                carrierData['volumeNo'] = jobList[3]

                # Process the carrier
                success = processDisc(carrierData)
                #success = processDiscTest(carrierData)

            if success and not endOfBatchFlag:
                # Remove job file
                os.remove(jobOldest)
            elif not endOfBatchFlag:
                # Move job file to failed jobs folder
                baseName = os.path.basename(jobOldest)
                os.rename(jobOldest, os.path.join(config.jobsFailedFolder, baseName))

        # Check if user pressed Exit, and quit if so ...
        if config.quitFlag:
            quitIromlab()
