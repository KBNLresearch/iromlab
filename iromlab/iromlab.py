#! /usr/bin/env python
import sys
import os
import imp
import xml.etree.ElementTree as ETree
import threading
import uuid
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
from kbapi import sru
import cdworker

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

        # Create failed jobs folder (if a job fails it will be moved here)
        config.jobsFailedFolder = os.path.join(config.batchFolder, 'jobsFailed')
        
        if not os.path.exists(config.jobsFailedFolder):

            try:
                os.makedirs(config.jobsFailedFolder)
            except IOError:
                msg = 'Cannot create failed jobs folder ' + config.jobsFailedFolder
                tkMessageBox.showerror("Error", msg)
        
        logFile = os.path.join(config.batchFolder, 'batch.log')
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
        config.jobsFailedFolder = os.path.join(config.batchFolder, 'jobsFailed')
        logFile = os.path.join(config.batchFolder, 'batch.log')
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
                #lineOut = ','.join([jobID, catid, '"' + title + '"', volumeNo, noVolumes, carrierType]) + '\n'
                lineOut = ','.join([jobID, catid, '"' + title + '"', volumeNo, carrierType]) + '\n'
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
        
        # Read configuration file
        getConfiguration()
        
def representsInt(s):
    # Source: http://stackoverflow.com/a/1267145
    try: 
        int(s)
        return True
    except ValueError:
        return False

def checkFileExists(fileIn):
    # Check if file exists and exit if not
    if os.path.isfile(fileIn) == False:
        msg = "file " + fileIn + " does not exist!"
        #errorExit(msg)
        tkMessageBox.showerror("Error", msg)
        sys.exit()
        
def checkDirExists(dirIn):
    # Check if directory exists and exit if not
    if os.path.isdir(dirIn) == False:
        msg = "directory " + dirIn + " does not exist!"
        #errorExit(msg)
        tkMessageBox.showerror("Error", msg)
        sys.exit()
        
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
    
    # Make logger variable global
    global logging
    
    root = tk.Tk()
    carrierEntry(root)
    
    t1 = threading.Thread(target=cdworker.cdWorker, args=[])
    t1.start()
    root.mainloop()
    t1.join()
        
main()