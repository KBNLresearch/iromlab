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
import uuid
import wmi # Dependency: python -m pip install wmi
import pythoncom
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
import isolyzer


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
                 
    def on_quit(self, event=None):
        # Wait until the disc that is currently being pocessed has 
        # finished, and quit (batch can be resumed by opening it in the File dialog)
        config.quitFlag = True
        self.bExit.config(state = 'disabled')
        quit()
    
    def on_create(self, event=None):
        # Create new batch
        
        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = config.rootDir
        options['mustexist'] = False
        options['parent'] = self.root
        options['title'] = 'Select batch directory'
        config.batchFolder = os.path.normpath(tkFileDialog.askdirectory(**self.dir_opt))
        
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
        
    def on_open(self, event=None):
        # Open existing batch
        
        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = config.rootDir
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
           
    def on_finalise(self, event=None):
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
            self.submit_button.config(state = 'disabled')
            quit()
 
    def on_submit(self, event=None):
            
        # Fetch entered values (strip any leading / tralue whitespace characters)   
        catid = self.catid_entry.get().strip()
        volumeNo = self.volumeNo_entry.get().strip()
        # noVolumes = self.noVolumes_entry.get().strip()
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
        #elif representsInt(noVolumes) == False:
        #    msg = "Number of volumes must be integer value"
        #    tkMessageBox.showerror("Type mismatch", msg)
        elif int(volumeNo) < 1:
            msg = "Volume number must be greater than or equal to 1"
            tkMessageBox.showerror("Value error", msg)
        #elif int(volumeNo) > int(noVolumes):
        #    msg = "Volume number cannot be larger than number of volumes"
        #    tkMessageBox.showerror("Value error", msg)
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
                # Create unique identifier for this job (UUID, based on host ID and current time)
                jobID = str(uuid.uuid1())
                # Create and populate Job file                      
                jobFile = ''.join([jobID,".txt"])
                fJob = open(os.path.join(config.jobsFolder, jobFile), "w")
                lineOut = ','.join([jobID, catid, '"' + title + '"', volumeNo, noVolumes, carrierType]) + '\n'
                fJob.write(lineOut)
                fJob.close()
                        
                # Reset entry fields        
                self.catid_entry.delete(0, tk.END)
                self.volumeNo_entry.delete(0, tk.END)
                #self.noVolumes_entry.delete(0, tk.END)
        
    def init_gui(self):
                        
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
        self.bNew = tk.Button(self, text="New", height=2, width=4, underline=0, command=self.on_create)
        self.bNew.grid(column=0, row=1, sticky='ew')
        self.bOpen = tk.Button(self, text="Open", height=2, width=4, underline=0, command=self.on_open)
        self.bOpen.grid(column=1, row=1, sticky='ew')
        self.bFinalise = tk.Button(self, text="Finalize", height=2, width=4, underline=0, command=self.on_finalise)
        self.bFinalise.grid(column=2, row=1, sticky='ew')
        self.bExit = tk.Button(self, text="Exit", height=2, width=4, underline=0, command=self.on_quit)
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

        """
        # Number of volumes
        tk.Label(self, text='Number of volumes').grid(column=0, row=6,
                sticky='w')
        self.noVolumes_entry = tk.Entry(self, width=5)
        self.noVolumes_entry.grid(column=1, row=6, sticky='w')
        """
        
        # Carrier type (radio button select)
        self.v = tk.IntVar()
        self.v.set(1)

        # List with all possible carrier types, corresponding button codes, keyboard shortcut character
        # (keyboard shortcuts not actually used yet)
        self.carrierTypes = [
            ['cd-rom',1,0],
            ['cd-audio',2,3],
            ['dvd-rom',3,0],
            ['dvd-video',4,4]
        ]        
        
        tk.Label(self, text='Carrier type').grid(column=0, row=6,
                sticky='w', columnspan=4)
                
        rowValue = 6
        
        for carrierType in self.carrierTypes:
            #self.rb = tk.Radiobutton(self, text=carrierType[0], variable=self.v, value=carrierType[1], underline=carrierType[2])
            self.rb = tk.Radiobutton(self, text=carrierType[0], variable=self.v, value=carrierType[1])
            self.rb.grid(column=1, row=rowValue, sticky='w')
            rowValue += 1
        
        self.submit_button = tk.Button(self, text='Submit', height=2, width=4, underline=0, bg = '#ded4db', state = 'disabled',
                command=self.on_submit)
        self.submit_button.grid(column=1, row=13, sticky='ew')
        
        # Define bindings for keyboard shortcuts: buttons
        self.root.bind_all('<Control-Key-n>', self.on_create)
        self.root.bind_all('<Control-Key-o>', self.on_open)
        self.root.bind_all('<Control-Key-f>', self.on_finalise)
        self.root.bind_all('<Control-Key-e>', self.on_quit)
        self.root.bind_all('<Control-Key-s>', self.on_submit)
        
        # TODO keyboard shortcuts for Radiobox selections: couldn't find ANY info on how to do this!
                
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)
                
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
    
    # Use CoInitialize to avoid errors like this:
    #    http://stackoverflow.com/questions/14428707/python-function-is-unable-to-run-in-new-thread
    pythoncom.CoInitialize()
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
    
    # extract volume identifier from ISO's Primary Volume Descriptor
    try:
        isolyzerResult = isolyzer.processImage(isoFile)
        volumeIdentifier = isolyzerResult.findtext('properties/primaryVolumeDescriptor/volumeIdentifier')
    except IOError:
        volumeIdentifier = ''

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log
    dictOut["volumeIdentifier"] = volumeIdentifier
        
    return(dictOut)

def isoBusterRipAudio(writeDirectory, session):
    # Rip audio to WAV (to be replaced by dBPoweramp wrapper in final version)
    # IsoBuster /d:i /ei:"E:\nimbieTest\" /et:wav /ep:oea /ep:npc /c /m /nosplash /s:1 /t:audio /l:"E:\nimbieTest\ib.log"
    # IMPORTANT: the /t:audio switch requires IsoBuster 3.9 (currently in beta) or above!    
    
    logFile = ''.join([config.tempDir,shared.randomString(12),".log"])

    args = [config.isoBusterExe]
    args.append("".join(["/d:", config.cdDriveLetter, ":"]))
    args.append("".join(["/ei:", writeDirectory]))
    args.append("/et:wav")
    args.append("/ep:oea")
    args.append("/ep:npc")
    args.append("/c")
    args.append("/m")
    args.append("/nosplash")
    args.append("".join(["/s:",str(session)]))
    args.append("/t:audio")
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

def processDisc(carrierData):

    jobID = carrierData['jobID']
    
    logging.info(''.join(['### Job identifier: ', jobID]))
    logging.info(''.join(['PPN: ',carrierData['PPN']]))
    logging.info(''.join(['Title: ',carrierData['title']]))
    logging.info(''.join(['Volume number: ',carrierData['volumeNo']]))
    
        
    # Initialise reject and success status
    reject = False
    success = True
    
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
        success = False
        logging.error(''.join(['drive ', config.cdDriveLetter, ' does not exist']))
            
    if discLoaded == False:
        print("--- Entering  reject")
        success = False
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
        dirDisc = os.path.join(config.batchFolder, jobID)
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
            # TODO: replace by dBpoweramp wrapper in  production version
            # Also IsoBuster (3.8.0) erroneously extracts data from any data sessions here as well
            # (and saves file with .wav file extension!)
            dirOut = os.path.join(dirDisc, "audio")
            if not os.path.exists(dirOut):
                os.makedirs(dirOut)
                
            resultIsoBuster = isoBusterRipAudio(dirOut, 1)
            checksumDirectory(dirOut)
            
            statusIsoBuster = resultIsoBuster["log"].strip()
              
            if statusIsoBuster != "0":
                success = False
                reject = True
                logging.error("Isobuster exited with error(s)")

            logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
            logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
            logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
                
            if carrierInfo["cdExtra"] == True and carrierInfo["containsData"] == True:
                logging.info('*** Extracting data session of cdExtra to ISO ***')
                print("--- Extract data session of cdExtra to ISO")
                # Create ISO file from data on 2nd session
                dirOut = os.path.join(dirDisc, "data")
                if not os.path.exists(dirOut):
                    os.makedirs(dirOut)
                
                resultIsoBuster = isoBusterExtract(dirOut, 2)
                checksumDirectory(dirOut)
                
                statusIsoBuster = resultIsoBuster["log"].strip()
                
                if statusIsoBuster != "0":
                    success = False
                    reject = True
                    logging.error("Isobuster exited with error(s)")
                
                logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
                logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
                logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
                
        elif carrierInfo["containsData"] == True:
            logging.info('*** Extract data session to ISO ***')
            # Create ISO image of first session
            dirOut = os.path.join(dirDisc, "data")
            if not os.path.exists(dirOut):
                os.makedirs(dirOut)
                
            resultIsoBuster = isoBusterExtract(dirOut, 1)
            checksumDirectory(dirOut)
            statusIsoBuster = resultIsoBuster["log"].strip()
            
            if resultIsoBuster["log"].strip() != "0":
                success = False
                reject = True
                logging.error("Isobuster exited with error(s)")
            
            logging.info(''.join(['isobuster command: ', resultIsoBuster['cmdStr']]))
            logging.info(''.join(['isobuster-status: ', str(resultIsoBuster['status'])]))
            logging.info(''.join(['isobuster-log: ', statusIsoBuster]))
            logging.info(''.join(['volumeIdentifier: ', str(resultIsoBuster['volumeIdentifier'])]))

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

        # Create comma-delimited batch manifest entry for this carrier
        
        # VolumeIdentifier only defined for ISOs 
        try:
            volumeID = resultIsoBuster['volumeIdentifier'].strip()
        except KeyError:
            volumeID = ''
            
        # Path to dirDisc, relative to batchFolder
        dirDiscRel = os.path.relpath(dirDisc, os.path.commonprefix([dirDisc, config.batchFolder])) 
        
        myCSVRow = ','.join([jobID, 
                            carrierData['PPN'], 
                            dirDiscRel,
                            carrierData['volumeNo'], 
                            carrierData['carrierType'],
                            carrierData['title'], 
                            '"' + volumeID + '"',
                            str(success)])
                            
        # Note: carrierType is value entered by user, NOT auto-detected value! Might need some changes.
            
        # Append entry to batch manifest
        bm = open(config.batchManifest,'a')
        bm.write(myCSVRow + '\n')
        bm.close()
        
def workerTest():

    # Dummy version of cdWorker function that doesn't do any actual imaging
    # used for testing only

    waitingForBatchDir = True

    # Loop periodically scans value of config.batchFolder
    while waitingForBatchDir == True:
        
        if config.batchFolder != '': 
            waitingForBatchDir = False
            logging.info(''.join(['batch folder set to ', config.batchFolder]))
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

def cdWorker():

    # Worker function that monitors the job queue and processes the discs in FIFO order 

    # Flag is True while batchFolder is undefined (variable set by user in GUI)
    waitingForBatchDir = True

    # Loop periodically scans value of config.batchFolder
    while waitingForBatchDir == True:
        
        if config.batchFolder != '': 
            waitingForBatchDir = False
            logging.info(''.join(['batchFolder set to ', config.batchFolder]))
        else:
            time.sleep(2)
            #print('waiting for batchFolder to be set ...')
    
    # Define batch manifest (CSV file with minimal metadata on each carrier)
    config.batchManifest = os.path.join(config.batchFolder, 'manifest.csv')
    
    # Write header row if batch manifest doesn't exist already
    if os.path.isfile(config.batchManifest) == False:
        myCSVRow = ','.join(['jobID', 
                            'PPN', 
                            'dirDisc',
                            'volumeNo', 
                            'carrierType',
                            'title', 
                            'volumeID',
                            'success'])
                                       
        # Write header to batch manifest
        bm = open(config.batchManifest,'a')
        bm.write(myCSVRow + '\n')
        bm.close()
        
    # Initialise batch
    logging.info('*** Initialising batch ***')
    resultPrebatch = drivers.prebatch()
    logging.info(''.join(['prebatch command: ', resultPrebatch['cmdStr']]))
    logging.info(''.join(['prebatch command output: ',resultPrebatch['log'].strip()]))
    
    # Flag that marks end of batch (main processing loop keeps running while False)
    endOfBatchFlag = False
    
    while endOfBatchFlag == False and config.quitFlag == False:
        time.sleep(2)
        # Get directory listing, sorted by creation time
        files = filter(os.path.isfile, glob.glob(config.jobsFolder + '/*'))
        files.sort(key=lambda x: os.path.getctime(x))
        
        noFiles = len(files)

        if noFiles > 0:
            # Identify oldest job file
            jobOldest = files[0]
            
            # Open job file and read contents 
            fj = open(jobOldest, "r")
            lines = fj.readlines()
            fj.close()
            if lines[0] == 'EOB\n':
                # End of current batch
                endOfBatchFlag = True
                quit()
            else:
                # Split items in job file to list
                jobList = lines[0].strip().split(",")
                # Set up dictionary that holds carrier data
                carrierData = {}
                carrierData['jobID'] = jobList[0]
                carrierData['PPN'] = jobList[1]
                carrierData['title'] = jobList[2]
                carrierData['volumeNo'] = jobList[3]
                #carrierData['noVolumes'] = jobList[4]
                carrierData['carrierType'] = jobList[4]
                
                # Process the carrier
                processDisc(carrierData)
            
            # Remove job file
            # TODO: if job resulted in errors it may be better to move the job file to an 'error'
            # folder instead of removing it altogether!
            os.remove(jobOldest)


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
    tempDir = "C:/Temp/"
    rootDir = "E:/nimbieTest"
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
    config.tempDir = os.path.normpath(tempDir)
    config.rootDir = os.path.normpath(rootDir)
    config.secondsToTimeout = secondsToTimeout
    
    # Make logger variable global
    global logging
    
    root = tk.Tk()
    carrierEntry(root)
    
    t1 = threading.Thread(target=cdWorker, args=[])
    t1.start()
    root.mainloop()
    t1.join()
        
main()