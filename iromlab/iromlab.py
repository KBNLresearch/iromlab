#! /usr/bin/env python
from pkg_resources import Requirement, resource_filename
import sys
import os
from shutil import copyfile
import imp
import glob
import time
import xml.etree.ElementTree as ETree
import threading
import uuid
import logging
try:
    import tkinter as tk #Python 3.x
    from tkinter import ttk as ttk
    from tkinter import filedialog as tkFileDialog
    from tkinter import scrolledtext as ScrolledText
    from tkinter import messagebox as tkMessageBox
except ImportError:
    import Tkinter as tk # Python 2.x
    import ttk as ttk
    import tkFileDialog
    import ScrolledText
    import tkMessageBox
import config
from kbapi import sru
import cdworker
import cdinfo

__version__ = '0.1.0'

"""
Script for automated imaging / ripping of optical media using a Nimbie disc robot.

Features:

* Automated load / unload  / reject using dBpoweramp driver binaries
* Disc type detection using libcdio's cd-info tool
* Data CDs and DVDs are imaged to ISO file using IsoBuster
* Audio CDs are ripped to WAV using IsoBuster (to be replaced with dBpoweramp later)  

Author: Johan van der Knijff
Research department,  KB / National Library of the Netherlands

"""
class carrierEntry(tk.Frame):

    # This class defines the graphical user interface + associated functions
    # for associated actions
    
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        config.readyToStart = False
        config.finishedBatch = False
        self.build_gui()
        
    def on_quit(self, event=None):
        # Wait until the disc that is currently being pocessed has 
        # finished, and quit (batch can be resumed by opening it in the File dialog)
        config.quitFlag = True
        self.bExit.config(state = 'disabled')
        msg = 'Quitting because user pressed Exit!'
        tkMessageBox.showinfo("Finished", msg)
        if config.readyToStart == False:
            os._exit(0)
        else:
            quit()
  
    def on_create(self, event=None):
        # Create new batch in rootDir
        
        # Create unique batch identifier (UUID, based on host ID and current time)
        # this ensures that if the software is run in parallel on different machines
        # the batch identifiers will always be unique
        batchID = str(uuid.uuid1())
        
        # Construct batch name
        batchName = config.prefixBatch + '-' + batchID
        config.batchFolder = os.path.join(config.rootDir, batchName)
        try:
            os.makedirs(config.batchFolder)
        except IOError:
            msg = 'Cannot create batch folder ' + config.batchFolder
            tkMessageBox.showerror("Error", msg)

        # Create jobs folder
        config.jobsFolder = os.path.join(config.batchFolder, 'jobs')
        try:
            os.makedirs(config.jobsFolder)
        except IOError:
            msg = 'Cannot create jobs folder ' + config.jobsFolder
            tkMessageBox.showerror("Error", msg)

        # Create failed jobs folder (if a job fails it will be moved here)
        config.jobsFailedFolder = os.path.join(config.batchFolder, 'jobsFailed')
        try:
            os.makedirs(config.jobsFailedFolder)
        except IOError:
            msg = 'Cannot create failed jobs folder ' + config.jobsFailedFolder
            tkMessageBox.showerror("Error", msg)
        
        # Set up logging
        self.setupLogging(self.text_handler)
        
        # Notify user
        msg = 'Created batch ' + batchName
        tkMessageBox.showinfo("Created batch", msg)
            
        # Update state of buttons
        self.bNew.config(state = 'disabled')
        self.bOpen.config(state = 'disabled')
        self.bFinalise.config(state = 'normal')
        self.submit_button.config(state = 'normal')
        config.readyToStart = True
         
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

        # Set up logging
        self.setupLogging(self.text_handler)
        
        if config.batchFolder != '':
            # Update state of buttons
            self.bNew.config(state = 'disabled')
            self.bOpen.config(state = 'disabled')
            self.bFinalise.config(state = 'normal')
            self.submit_button.config(state = 'normal')
            config.readyToStart = True
           
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
            #quit()
 
    def on_submit(self, event=None):
            
        # Fetch entered values (strip any leading / tralue whitespace characters)   
        catid = self.catid_entry.get().strip()
        volumeNo = self.volumeNo_entry.get().strip()
        carrierTypeCode = self.v.get()
        
        # Lookup carrierType for carrierTypeCode value
        for i in self.carrierTypes:
            if i[1] == carrierTypeCode:
                carrierType = i[0]
        
        # Lookup catalog identifier
        sruSearchString = '"PPN=' + str(catid) + '"'
        response = sru.search(sruSearchString,"GGC")
        noGGCRecords = response.sru.nr_of_records
        
        if config.readyToStart == False:
            msg = "You must first create a batch or open an existing batch"
            tkMessageBox.showerror("Not ready", msg)
        elif representsInt(volumeNo) == False:
            msg = "Volume number must be integer value"
            tkMessageBox.showerror("Type mismatch", msg)
        elif int(volumeNo) < 1:
            msg = "Volume number must be greater than or equal to 1"
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
                # Prompt operator to insert carrier in disc robot
                msg = "Please load disc ('" + title + "', volume " + str(volumeNo) + \
                    ") into the disc loader, then press 'OK'"
                tkMessageBox.showinfo("Load disc", msg)
                
                # Create unique identifier for this job (UUID, based on host ID and current time)
                jobID = str(uuid.uuid1())
                # Create and populate Job file                      
                jobFile = ''.join([jobID,".txt"])
                fJob = open(os.path.join(config.jobsFolder, jobFile), "w")
                lineOut = ','.join([jobID, catid, '"' + title + '"', volumeNo, carrierType]) + '\n'
                fJob.write(lineOut)
                fJob.close()
                                
                # Reset entry fields        
                self.catid_entry.delete(0, tk.END)
                self.volumeNo_entry.delete(0, tk.END)
    
    def setupLogging(self, handler):
          
        # Set up log-related settings 
        logFile = os.path.join(config.batchFolder, 'batch.log')
        logging.basicConfig(filename=logFile, 
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s')
        # Add the handler to logger
        logger = logging.getLogger()
        logger.addHandler(handler)
    
    def build_gui(self):
                        
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
        
        # Disable finalise button on startup
        self.bFinalise.config(state = 'disabled')
                 
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
            self.rb = tk.Radiobutton(self, text=carrierType[0], variable=self.v, value=carrierType[1])
            self.rb.grid(column=1, row=rowValue, sticky='w')
            rowValue += 1
        
        self.submit_button = tk.Button(self, text='Submit', height=2, width=4, underline=0, bg = '#ded4db', state = 'disabled',
                command=self.on_submit)
        self.submit_button.grid(column=1, row=13, sticky='ew')

        # Add ScrolledText widget to display logging info
        st = ScrolledText.ScrolledText(self, state='disabled', height = 15)
        st.configure(font='TkFixedFont')
        st.grid(column=0, row=15, sticky='w', columnspan=4)

        # Create textLogger
        self.text_handler = TextHandler(st)
                                     
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

class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    
    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

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

    # Install configuration file to user dir if it is not there already.
    # Read configuration file, make all config variables available via
    # config.py and check that all file paths / executables exist.
    # This assumes an non-frozen script (no Py2Exe)

    # From where is this script executed?)
    rootPath = os.path.abspath(get_main_dir())
    # Locate Windows user directory
    userDir = os.path.expanduser('~')
    # Config directory
    configDir = os.path.join(userDir,'iromlab')
    
    # Create config directory if it doesn't exist
    if os.path.isdir(configDir) == False:
        try:
            os.makedirs(configDir)
        except IOError:
            msg = 'could not create configuration directory'
            errorExit(msg)

    # Config file name
    configFile = os.path.join(configDir,'config.xml')
    
    if os.path.isfile(configFile) == False:
        # No config file in user dir, so we copy it from the source. Location depends on whether
        # iromlab is run from deployment or development location
        try:
            # Installed via setup.py / pip: need to extract config file from egg
            configFileSource = resource_filename(Requirement.parse('iromlab'),'conf/config.xml')
            print(configFileSource)
        except KeyError:
            # We end up here  if iromlab is run from development location. In this  case
            # the config file is located in /conf directory
            configFileSource =  os.path.join(rootPath,'conf','config.xml')
            print(configFileSource)
        # Copy source config file to user dir 
        try:
            copyfile(configFileSource, configFile)
        except IOError:
            msg = 'could not copy configuration file to ' + configFile
            errorExit(msg)

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
    config.prefixBatch = findElementText(configElt, './config/prefixBatch')
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
    
    # Check that cdDriveLetter points to an existing optical drive  
    resultGetDrives = cdinfo.getDrives()
    cdDrives = resultGetDrives["drives"]
    if config.cdDriveLetter not in cdDrives:
        msg = '"' + config.cdDriveLetter + '" is not a valid optical drive!'
        tkMessageBox.showerror("Error", msg)
        sys.exit()
    
def main():

    try:           
        root = tk.Tk()
        carrierEntry(root)
        
        t1 = threading.Thread(target=cdworker.cdWorker, args=[])
        t1.start()
            
        root.mainloop()
        t1.join()
    except KeyboardInterrupt:
        if config.finishedBatch == True:
            # Batch finished: notify user
            msg = 'Completed processing this batch, click OK to exit'
            tkMessageBox.showinfo("Finished", msg)
        os._exit(0)
main()