#! /usr/bin/env python
import sys
import os
import time
import imp
import glob
import codecs
import xml.etree.ElementTree as ETree
import drivers
import win32api
import threading
import wmi # Dependency: python -m pip install wmi
import pprint
import hashlib
import logging
try:
    import tkinter as tk #Python 3.x
    from tkinter import ttk as ttk
    import filedialog as tkFileDialog
except ImportError:
    import Tkinter as tk # Python 2.x
    import ttk as ttk
    import tkFileDialog
import tkMessageBox
import config
import shared
from kbapi import sru


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
class carrierEntry(tk.Frame):

    # This class defines the graphical user interface + associated functions
    # for associated actions
    
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.readyToStart = False
        self.init_gui()
                 
    def on_quit(self):
        # Wait until the disc that is currently being pocessed has 
        # finished, and quit (batch can be resumed by opening it in the File dialog)
        config.quitFlag = True
        self.bExit.config(state = 'disabled')
        quit()
    
    def on_create(self):
        # Create new batch
        
        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = 'E:\\'
        options['mustexist'] = False
        options['parent'] = self.root
        options['title'] = 'Select batch directory'
        config.batchFolder = tkFileDialog.askdirectory(**self.dir_opt)
        
        # Create batch folder if it doesn't exist already
        if not os.path.exists(config.batchFolder):
            try:
                os.makedirs(config.batchFolder)
            except IOError:
                msg = 'Cannot create batch folder ' + config.batchFolder
                tkMessageBox.showerror("Error", msg)

        # Create jobs folder
        config.jobsFolder = os.path.join(config.batchFolder, 'jobs')
        
        if not os.path.exists(config.jobsFolder):
      
            try:
                os.makedirs(config.jobsFolder)
            except IOError:
                msg = 'Cannot create jobs folder ' + config.jobsFolder
                tkMessageBox.showerror("Error", msg)
                
        logFile = os.path.join(config.batchFolder, "batch.log")
        logging.basicConfig(filename=logFile, 
            level=logging.DEBUG, 
            format='%(asctime)s - %(levelname)s - %(message)s')
            
        # Update state of buttons
        self.bNew.config(state = 'disabled')
        self.bOpen.config(state = 'disabled')
        self.submit_button.config(state = 'normal')
        self.readyToStart = True
        
    def on_open(self):
        # Open existing batch
        
        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = 'E:\\nimbieTest'
        options['mustexist'] = True
        options['parent'] = self.root
        options['title'] = 'Select batch directory'
        config.batchFolder = tkFileDialog.askdirectory(**self.dir_opt)
        config.jobsFolder = os.path.join(config.batchFolder, 'jobs')
        logFile = os.path.join(config.batchFolder, "batch.log")
        logging.basicConfig(filename=logFile, 
            level=logging.DEBUG, 
            format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Update state of buttons
        self.bNew.config(state = 'disabled')
        self.bOpen.config(state = 'disabled')
        self.submit_button.config(state = 'normal')
        self.readyToStart = True
           
    def on_finalise(self):
        msg = "This will finalise the current batch.\n After finalising no further carriers can be \n \
        added. Are you really sure you want to do this?"
        if tkMessageBox.askyesno("Confirm", msg):
            # Create End Of Batch job file; this will tell the main worker processing 
            # loop to stop
                        
            jobFile = 'eob.txt' 
            fJob = open(os.path.join(config.jobsFolder, jobFile), "w")
            lineOut = 'EOB\n'
            fJob.write(lineOut)
            self.bFinalise.config(state = 'disabled')
            quit()
 
    def submit(self):
            
        # Fetch entered values (strip any leading / tralue whitespace characters)   
        catid = self.catid_entry.get().strip()
        volumeNo = self.volumeNo_entry.get().strip()
        noVolumes = self.noVolumes_entry.get().strip()
        carrierTypeCode = self.v.get()
        
        # Lookup carrierType for carrierTypeCode value
        for i in self.carrierTypes:
            if i[1] == carrierTypeCode:
                carrierType = i[0]
        
        # Lookup catalog identifier
        sruSearchString = '"PPN=' + str(catid) + '"'
        response = sru.search(sruSearchString,"GGC")
        noGGCRecords = response.sru.nr_of_records
        
        if self.readyToStart == False:
            msg = "You must first create a batch or open an existing batch"
            tkMessageBox.showerror("Not ready", msg)
        elif representsInt(volumeNo) == False:
            msg = "Volume number must be integer value"
            tkMessageBox.showerror("Type mismatch", msg)
        elif representsInt(noVolumes) == False:
            msg = "Number of volumes must be integer value"
            tkMessageBox.showerror("Type mismatch", msg)
        elif int(volumeNo) < 1:
            msg = "Volume number must be greater than or equal to 1"
            tkMessageBox.showerror("Value error", msg)
        elif int(volumeNo) > int(noVolumes):
            msg = "Volume number cannot be larger than number of volumes"
            tkMessageBox.showerror("Value error", msg)
        elif noGGCRecords == 0:
            # No matching record found
            msg = ("Search for PPN=" + str(catid) + " returned " + \
                "no matching record in catalog!")
            tkMessageBox.showerror("PPN not found", msg)
        else:
            # Matching record found. Display title and ask for confirmation
            record = next(response.records)
            title = record.titles[0]
            msg = "Found title:\n\n'" + title + "'.\n\n Is this correct?"
            if tkMessageBox.askyesno("Confirm", msg):
                # Job file
                               
                jobFile = ''.join([shared.randomString(12),".txt"])
                fJob = open(os.path.join(config.jobsFolder, jobFile), "w")
                lineOut = ','.join([catid, volumeNo, noVolumes, carrierType]) + '\n'
                fJob.write(lineOut)
                        
                # Reset entry fields        
                self.catid_entry.delete(0, tk.END)
                self.volumeNo_entry.delete(0, tk.END)
                self.noVolumes_entry.delete(0, tk.END)
        
    def init_gui(self):
        
        # List with all possible carrier types + corresponding button codes
        self.carrierTypes = [
            ['cd-rom',1],
            ['cd-audio',2],
            ['dvd-rom',3],
            ['dvd-video',4]
        ]
        
        # Build GUI
        self.root.title('iromlab')
        self.root.option_add('*tearOff', 'FALSE')
 
        #self.grid(column=0, row=0, sticky='nsew')
        self.grid(column=0, row=0, sticky='ew')
        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')
       
        # Batch toolbar     
        self.bNew = tk.Button(self, text="New", height=2, width=4, command=self.on_create)
        self.bNew.grid(column=0, row=1, sticky='ew')
        self.bOpen = tk.Button(self, text="Open", height=2, width=4, command=self.on_open)
        self.bOpen.grid(column=1, row=1, sticky='ew')
        self.bFinalise = tk.Button(self, text="Finalize", height=2, width=4, command=self.on_finalise)
        self.bFinalise.grid(column=2, row=1, sticky='ew')
        self.bExit = tk.Button(self, text="Exit", height=2, width=4, command=self.on_quit)
        self.bExit.grid(column=3, row=1, sticky='ew')
                 
        # Entry elements for each carrier
   
        # Catalog ID        
        tk.Label(self, text='PPN').grid(column=0, row=4,
                sticky='w')
        self.catid_entry = tk.Entry(self, width=12)
        self.catid_entry.grid(column=1, row = 4, sticky='w')

        # Volume number
        tk.Label(self, text='Volume number').grid(column=0, row=5,
                sticky='w')
        self.volumeNo_entry = tk.Entry(self, width=5)
        self.volumeNo_entry.grid(column=1, row=5, sticky='w')

        # Number of volumes
        tk.Label(self, text='Number of volumes').grid(column=0, row=6,
                sticky='w')
        self.noVolumes_entry = tk.Entry(self, width=5)
        self.noVolumes_entry.grid(column=1, row=6, sticky='w')
 
        # Carrier type (radio button select)
        self.v = tk.IntVar()
        self.v.set(1)
        
        tk.Label(self, text='Carrier type').grid(column=0, row=7,
                sticky='w', columnspan=4)
                
        rowValue = 7
        
        for carrierType in self.carrierTypes:
            self.rb = tk.Radiobutton(self, text=carrierType[0], variable=self.v, value=carrierType[1]).grid(column=1, row=rowValue, 
            sticky='w')
            rowValue += 1
        
        self.submit_button = tk.Button(self, text='Submit', height=2, width=4, bg = '#ded4db', state = 'disabled',
                command=self.submit)
        self.submit_button.grid(column=1, row=13, sticky='ew')
                
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)


def workerTest():

    preBatch = True

    # Loop periodically scans value of config.batchFolder
    while preBatch == True:
        
        if config.batchFolder != '': 
            preBatch = False
            print('batchFolder set to ' + config.batchFolder)
        else:
            time.sleep(2)
            print('waiting for batchFolder to be set ...')
    
    # Flag that marks end of batch (main processing loop keeps running while False)
    endOfBatchFlag = False
    
    while endOfBatchFlag == False and config.quitFlag == False:
        time.sleep(10)
        # Get directory listing, sorted by creation time
        files = filter(os.path.isfile, glob.glob(config.jobsFolder + '/*'))
        files.sort(key=lambda x: os.path.getctime(x))
        
        noFiles = len(files)
        print(noFiles)

        if noFiles > 0:
            # Identify oldest file
            fileOldest = files[0]
            
            # Open file and read contents 
            fOldest = open(fileOldest, "r")
            lines = fOldest.readlines()
            fOldest.close()
            print(lines)
            # Remove file
            os.remove(fileOldest)
            
            if lines[0] == 'EOB\n':
                # End of current batch
                endOfBatchFlag = True
                quit()
                 
def representsInt(s):
    # Source: http://stackoverflow.com/a/1267145
    try: 
        int(s)
        return True
    except ValueError:
        return False

def errorExit(error, terminal):
    terminal.write("Error - " + error + "\n")
    sys.exit()

def mediumLoaded(driveName):
    # Returns True if medium is loaded (also if blank/unredable), False if not
    c = wmi.WMI()
    foundDriveName = False
    loaded = False
    for cdrom in c.Win32_CDROMDrive():
        if cdrom.Drive == driveName:
            foundDriveName = True
            loaded = cdrom.MediaLoaded       
    
    return(foundDriveName, loaded)
    
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
    
    # Test if disc is loaded
    discLoaded = False
    
    print("--- Entering  driveIsReady loop")
    
    # Reject if no CD is found after 20 s
    timeout = time.time() + int(config.secondsToTimeout)
    while discLoaded == False and time.time() < timeout:
        # Timeout value prevents infinite loop in case of unreadable disc
        time.sleep(2)
        foundDrive, discLoaded = mediumLoaded(config.cdDriveLetter + ":")

    if foundDrive == False:
        logging.error(''.join(['drive ', config.cdDriveLetter, ' does not exist']))
    
    if discLoaded == False:
        print("--- Entering  reject")
        resultReject = drivers.reject()
        logging.error('no disc loaded')
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
        # UPDATE: Case 1. can be eliminated if loading of a CD is made dependent of
        # a queue of disc ids (which are entered by operator at time of adding a CD)
        #
        # In that case:
        #
        # queue is empty --> no CD in loader --> pause loading until new item in queue
        #
        # (Can still go wrong if items are entered in queue w/o loading any CDs, but
        # this is an edge case)
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
            resultShnTool = cdrdaoExtract(dirOut, 1)
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

        
def mainOld():

    # Configuration (move to config file later)
    cdDriveLetter = "J"
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
    secondsToTimeout = "20"
    
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
    config.secondsToTimeout = secondsToTimeout

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
    ids = ["001", "002", "003"]
    
    # Set up queue
    q = queue.Queue()
    
    # Fill the queue
    for id in ids:
        q.put(id)
    
    for id in ids:
        # Process disc
        processDisc(q.get())

def main():

    # Configuration (move to config file later)
    cdDriveLetter = "J"
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
    secondsToTimeout = "20"
    
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
    config.secondsToTimeout = secondsToTimeout
    
    # Make logger variable global
    global logging

    root = tk.Tk()
    carrierEntry(root)
    
    t1 = threading.Thread(target=workerTest, args=[])
    t1.start()
    root.mainloop()
    t1.join()
        
main()