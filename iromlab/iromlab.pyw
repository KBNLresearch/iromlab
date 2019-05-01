#! /usr/bin/env python
"""
Script for automated imaging / ripping of optical media using a Nimbie disc robot.

Features:

* Automated load / unload  / reject using dBpoweramp driver binaries
* Disc type detection using libcdio's cd-info tool
* Data CDs and DVDs are imaged to ISO file using IsoBuster
* Audio CDs are ripped to WAV or FLAC using dBpoweramp

Author: Johan van der Knijff
Research department,  KB / National Library of the Netherlands

"""

import sys
import os
import csv
import imp
import time
import xml.etree.ElementTree as ETree
import threading
import uuid
import logging
import queue
try:
    import tkinter as tk  # Python 3.x
    from tkinter import filedialog as tkFileDialog
    from tkinter import scrolledtext as ScrolledText
    from tkinter import messagebox as tkMessageBox
except ImportError:
    import Tkinter as tk  # Python 2.x
    import tkFileDialog
    import ScrolledText
    import tkMessageBox
from . import config
from .kbapi import sru
from . import cdworker
from . import cdinfo


__version__ = '0.11.0'


class carrierEntry(tk.Frame):

    """This class defines the graphical user interface + associated functions
    for associated actions
    """

    def __init__(self, parent, *args, **kwargs):
        """Initiate class"""
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        # Logging stuff
        self.logger = logging.getLogger()
        # Create a logging handler using a queue
        self.log_queue = queue.Queue(-1)
        self.queue_handler = QueueHandler(self.log_queue)
        config.readyToStart = False
        config.finishedBatch = False
        self.catidOld = ""
        self.titleOld = ""
        self.volumeNoOld = ""
        self.build_gui()

    def on_quit(self, event=None):
        """Wait until the disc that is currently being pocessed has
        finished, and quit (batch can be resumed by opening it in the File dialog)
        """
        config.quitFlag = True
        self.bExit.config(state='disabled')
        self.bFinalise.config(state='disabled')
        msg = 'User pressed Exit, quitting after current disc has been processed'
        tkMessageBox.showinfo("Info", msg)
        if not config.readyToStart:
            # Wait 2 seconds to avoid race condition
            time.sleep(2)
            msg = 'Quitting because user pressed Exit, click OK to exit'
            tkMessageBox.showinfo("Exit", msg)
            os._exit(0)

    def on_create(self, event=None):
        """Create new batch in rootDir"""

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
        successLogger = True

        try:
            self.setupLogger()
            # Start polling log messages from the queue
            self.after(100, self.poll_log_queue)
        except OSError:
            # Something went wrong while trying to write to lof file
            msg = ('error trying to write log file')
            tkMessageBox.showerror("ERROR", msg)
            successLogger = False

        if successLogger:
            # Notify user
            msg = 'Created batch ' + batchName
            tkMessageBox.showinfo("Created batch", msg)

            # Update state of buttons
            self.bNew.config(state='disabled')
            self.bOpen.config(state='disabled')
            self.bFinalise.config(state='normal')
            self.submit_button.config(state='normal')
            config.readyToStart = True


    def on_open(self, event=None):
        """Open existing batch"""

        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = config.rootDir
        options['mustexist'] = True
        options['parent'] = self.root
        options['title'] = 'Select batch directory'
        config.batchFolder = tkFileDialog.askdirectory(**self.dir_opt)
        config.jobsFolder = os.path.join(config.batchFolder, 'jobs')
        config.jobsFailedFolder = os.path.join(config.batchFolder, 'jobsFailed')

        # Check if batch was already finalized, and exit if so 
        if not os.path.isdir(config.jobsFolder):
            msg = 'cannot open finalized batch'
            tkMessageBox.showerror("Error", msg)
            #errorExit(msg)
            #quit()
            #os._exit(0)
        else:
            # Set up logging
            successLogger = True

            try:
                self.setupLogger()
                # Start polling log messages from the queue
                self.after(100, self.poll_log_queue)
            except OSError:
                # Something went wrong while trying to write to lof file
                msg = ('error trying to write log file')
                tkMessageBox.showerror("ERROR", msg)
                successLogger = False

            if successLogger:
                logging.info(''.join(['*** Opening existing batch ', config.batchFolder, ' ***']))

                if config.batchFolder != '':
                    # Update state of buttons, taking into account whether batch was
                    # finalized by user
                    self.bNew.config(state='disabled')
                    self.bOpen.config(state='disabled')
                    if os.path.isfile(os.path.join(config.jobsFolder, 'eob.txt')):
                        self.bFinalise.config(state='disabled')
                        self.submit_button.config(state='disabled')
                    else:
                        self.bFinalise.config(state='normal')
                        self.submit_button.config(state='normal')

                    # Set readyToStart
                    config.readyToStart = True


    def on_finalise(self, event=None):
        """Finalise batch after user pressed finalise button"""
        msg = ("This will finalise the current batch.\n After finalising no further"
               "carriers can be \nadded. Are you really sure you want to do this?")
        if tkMessageBox.askyesno("Confirm", msg):
            # Create End Of Batch job file; this will tell the main worker processing
            # loop to stop

            jobFile = 'eob.txt'
            fJob = open(os.path.join(config.jobsFolder, jobFile), "w", encoding="utf-8")
            lineOut = 'EOB\n'
            fJob.write(lineOut)
            self.bFinalise.config(state='disabled')
            self.submit_button.config(state='disabled')

    def on_usepreviousPPN(self, event=None):
        """Add previously entered PPN to entry field"""
        self.catid_entry.insert(tk.END, self.catidOld)

    def on_usepreviousTitle(self, event=None):
        """Add previously entered title to title field"""
        self.title_entry.insert(tk.END, self.titleOld)

    def on_increaseVolumeNumber(self, event=None):
        """Increase volume number from previous value"""
        if self.volumeNoOld == "":
            # No previous volume number
            msg = "Previous volume number is not defined"
            tkMessageBox.showerror("Cannot increase previous", msg)
        elif config.enablePPNLookup and self.catid_entry.get().strip() == "":
            # No PPN entered
            msg = "PPN is not defined"
            tkMessageBox.showerror("No PPN", msg)
        elif config.enablePPNLookup and self.catid_entry.get().strip() != self.catidOld:
            # New PPN
            msg = "New PPN, cannot increase from previous"
            tkMessageBox.showerror("New PPN", msg)
        elif not config.enablePPNLookup and self.title_entry.get().strip() == "":
            # No title entered
            msg = "Title is not defined"
            tkMessageBox.showerror("No title", msg)
        elif not config.enablePPNLookup and self.title_entry.get().strip() != self.titleOld:
            # New title
            msg = "New title, cannot increase from previous"
            tkMessageBox.showerror("New title", msg)
        else:
            volumeNoNew = str(int(self.volumeNoOld) + 1)
            self.volumeNo_entry.insert(tk.END, volumeNoNew)

    def on_submit(self, event=None):
        """Process one record and add it to the queue after user pressed submit button"""

        # Fetch entered values (strip any leading / tralue whitespace characters)
        if config.enablePPNLookup:
            catid = self.catid_entry.get().strip()
            self.catidOld = catid
        else:
            catid = ""
            title = self.title_entry.get().strip()
            self.titleOld = title
        volumeNo = self.volumeNo_entry.get().strip()
        self.volumeNoOld = volumeNo
        carrierTypeCode = self.v.get()

        # Lookup carrierType for carrierTypeCode value
        for i in self.carrierTypes:
            if i[1] == carrierTypeCode:
                carrierType = i[0]

        if config.enablePPNLookup:
            # Lookup catalog identifier
            sruSearchString = '"PPN=' + str(catid) + '"'
            response = sru.search(sruSearchString, "GGC")

            if not response:
                noGGCRecords = 0
            else:
                noGGCRecords = response.sru.nr_of_records
        else:
            noGGCRecords = 1

        if not config.readyToStart:
            msg = "You must first create a batch or open an existing batch"
            tkMessageBox.showerror("Not ready", msg)
        elif not representsInt(volumeNo):
            msg = "Volume number must be integer value"
            tkMessageBox.showerror("Type mismatch", msg)
        elif int(volumeNo) < 1:
            msg = "Volume number must be greater than or equal to 1"
            tkMessageBox.showerror("Value error", msg)
        elif noGGCRecords == 0:
            # No matching record found
            msg = ("Search for PPN=" + str(catid) + " returned " +
                   "no matching record in catalog!")
            tkMessageBox.showerror("PPN not found", msg)
        else:
            if config.enablePPNLookup:
                # Matching record found. Display title and ask for confirmation
                record = next(response.records)

                # Title can be in either in:
                # 1. title element
                # 2. title element with maintitle attribute
                # 3. title element with intermediatetitle attribute (3 in combination with 2)

                titlesMain = record.titlesMain
                titlesIntermediate = record.titlesIntermediate
                titles = record.titles

                if titlesMain != []:
                    title = titlesMain[0]
                    if titlesIntermediate != []:
                        title = title + ", " + titlesIntermediate[0]
                else:
                    title = titles[0]

            msg = "Found title:\n\n'" + title + "'.\n\n Is this correct?"
            if tkMessageBox.askyesno("Confirm", msg):
                # Prompt operator to insert carrier in disc robot
                msg = ("Please load disc ('" + title + "', volume " + str(volumeNo) +
                       ") into the disc loader, then press 'OK'")
                tkMessageBox.showinfo("Load disc", msg)

                # Create unique identifier for this job (UUID, based on host ID and current time)
                jobID = str(uuid.uuid1())
                # Create and populate Job file
                jobFile = os.path.join(config.jobsFolder, jobID + ".txt")

                if sys.version.startswith('3'):
                    # Py3: csv.reader expects file opened in text mode
                    fJob = open(jobFile, "w", encoding="utf-8")
                elif sys.version.startswith('2'):
                    # Py2: csv.reader expects file opened in binary mode
                    fJob = open(jobFile, "wb")

                # Create CSV writer object
                jobCSV = csv.writer(fJob, lineterminator='\n')

                # Row items to list
                rowItems = ([jobID, catid, title, volumeNo, carrierType])

                # Write row to job and close file
                jobCSV.writerow(rowItems)
                fJob.close()

                # Reset entry fields and set focus on PPN / Title field
                if config.enablePPNLookup:
                    self.catid_entry.delete(0, tk.END)
                    self.catid_entry.focus_set()
                else:
                    self.title_entry.delete(0, tk.END)
                    self.title_entry.focus_set()
                self.volumeNo_entry.delete(0, tk.END)

    def setupLogger(self):
        """Set up logging-related settings"""
        logFile = os.path.join(config.batchFolder, 'batch.log')

        logging.basicConfig(handlers=[logging.FileHandler(logFile, 'a', 'utf-8')],
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        # Add the handler to logger
        self.logger = logging.getLogger()
        # This sets the console output format (slightly different from basicConfig!)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        self.logger.addHandler(self.queue_handler)


    def display(self, record):
        """Display log record in scrolledText widget"""
        msg = self.queue_handler.format(record)
        self.st.configure(state='normal')
        self.st.insert(tk.END, msg + '\n', record.levelname)
        self.st.configure(state='disabled')
        # Autoscroll to the bottom
        self.st.yview(tk.END)


    def poll_log_queue(self):
        """Check every 100ms if there is a new message in the queue to display"""
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.after(100, self.poll_log_queue)


    def build_gui(self):
        """Build the GUI"""
        
        # Read configuration file
        getConfiguration()
        
        self.root.title('iromlab')
        self.root.option_add('*tearOff', 'FALSE')
        self.grid(column=0, row=0, sticky='ew')
        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')

        # Batch toolbar
        self.bNew = tk.Button(self,
                              text="New",
                              height=2,
                              width=4,
                              underline=0,
                              command=self.on_create)
        self.bNew.grid(column=0, row=1, sticky='ew')
        self.bOpen = tk.Button(self,
                               text="Open",
                               height=2,
                               width=4,
                               underline=0,
                               command=self.on_open)
        self.bOpen.grid(column=1, row=1, sticky='ew')
        self.bFinalise = tk.Button(self,
                                   text="Finalize",
                                   height=2,
                                   width=4,
                                   underline=0,
                                   command=self.on_finalise)
        self.bFinalise.grid(column=2, row=1, sticky='ew')
        self.bExit = tk.Button(self,
                               text="Exit",
                               height=2,
                               width=4,
                               underline=0,
                               command=self.on_quit)
        self.bExit.grid(column=3, row=1, sticky='ew')

        # Disable finalise button on startup
        self.bFinalise.config(state='disabled')

        # Entry elements for each carrier

        if config.enablePPNLookup:
            # Catalog ID (PPN)
            tk.Label(self, text='PPN').grid(column=0, row=4, sticky='w')
            self.catid_entry = tk.Entry(self, width=20)

            # Pressing this button adds previously entered PPN to entry field
            self.usepreviousPPN_button = tk.Button(self,
                               text='Use previous',
                               height=1,
                               width=2,
                               underline=0,
                               bg='#ded4db',
                               state='normal',
                               command=self.on_usepreviousPPN)
            self.usepreviousPPN_button.grid(column=2, row=4, sticky='ew')

            self.catid_entry.grid(column=1, row=4, sticky='w')
        else:
            # PPN lookup disabled, so present Title entry field
            tk.Label(self, text='Title').grid(column=0, row=4, sticky='w')
            self.title_entry = tk.Entry(self, width=45)

            # Pressing this button adds previously entered title to entry field
            self.usepreviousTitle_button = tk.Button(self,
                               text='Use previous',
                               height=1,
                               width=2,
                               underline=0,
                               bg='#ded4db',
                               state='normal',
                               command=self.on_usepreviousTitle)
            self.usepreviousTitle_button.grid(column=3, row=4, sticky='ew')
            self.title_entry.grid(column=1, row=4, sticky='w', columnspan=3)

        # Volume number
        tk.Label(self, text='Volume number').grid(column=0, row=5, sticky='w')
        self.volumeNo_entry = tk.Entry(self, width=5)
        
        # Pressing this button increases volume number from previous value
        self.increaseVolumeNumber_button = tk.Button(self,
                           text='Increase previous',
                           height=1,
                           width=2,
                           underline=0,
                           bg='#ded4db',
                           state='normal',
                           command=self.on_increaseVolumeNumber)
        self.increaseVolumeNumber_button.grid(column=3, row=5, sticky='ew')

        self.volumeNo_entry.grid(column=1, row=5, sticky='w')

        # Carrier type (radio button select)
        self.v = tk.IntVar()
        self.v.set(1)

        # List with all possible carrier types, corresponding button codes, keyboard
        # shortcut character (keyboard shortcuts not actually used yet)
        self.carrierTypes = [
            ['cd-rom', 1, 0],
            ['cd-audio', 2, 3],
            ['dvd-rom', 3, 0],
            ['dvd-video', 4, 4]
        ]

        tk.Label(self, text='Carrier type').grid(column=0, row=6, sticky='w', columnspan=4)

        rowValue = 6

        for carrierType in self.carrierTypes:
            self.rb = tk.Radiobutton(self,
                                     text=carrierType[0],
                                     variable=self.v,
                                     value=carrierType[1])
            self.rb.grid(column=1, row=rowValue, sticky='w')
            rowValue += 1

        self.submit_button = tk.Button(self,
                                       text='Submit',
                                       height=2,
                                       width=4,
                                       underline=0,
                                       bg='#ded4db',
                                       state='disabled',
                                       command=self.on_submit)
        self.submit_button.grid(column=1, row=13, sticky='ew')

        # Add ScrolledText widget to display logging info
        self.st = ScrolledText.ScrolledText(self, state='disabled', height=15)
        self.st.configure(font='TkFixedFont')
        self.st.grid(column=0, row=15, sticky='w', columnspan=4)

        # Define bindings for keyboard shortcuts: buttons
        self.root.bind_all('<Control-Key-n>', self.on_create)
        self.root.bind_all('<Control-Key-o>', self.on_open)
        self.root.bind_all('<Control-Key-f>', self.on_finalise)
        self.root.bind_all('<Control-Key-e>', self.on_quit)
        self.root.bind_all('<Control-Key-s>', self.on_submit)

        # TODO keyboard shortcuts for Radiobox selections: couldn't find ANY info on how to do this!

        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def reset_gui(self):
        """Reset the GUI"""
        # Logging stuff
        self.logger = logging.getLogger()
        # Create a logging handler using a queue
        self.log_queue = queue.Queue(-1)
        self.queue_handler = QueueHandler(self.log_queue)
        config.readyToStart = False
        config.finishedBatch = False
        self.catidOld = ""
        self.titleOld = ""
        self.volumeNoOld = ""

        self.bNew.config(state='normal')
        self.bOpen.config(state='normal')
        self.bFinalise.config(state='disabled')
        self.bExit.config(state='normal')
        self.submit_button.config(state='normal')

class QueueHandler(logging.Handler):
    """Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    Taken from https://github.com/beenje/tkinter-logging-text-widget/blob/master/main.py
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


def representsInt(s):
    """Return True if s is an integer, False otherwise"""
    # Source: http://stackoverflow.com/a/1267145
    try:
        int(s)
        return True
    except ValueError:
        return False


def checkFileExists(fileIn):
    """Check if file exists and exit if not"""
    if not os.path.isfile(fileIn):
        msg = "file " + fileIn + " does not exist!"
        tkMessageBox.showerror("Error", msg)
        sys.exit()


def checkDirExists(dirIn):
    """Check if directory exists and exit if not"""
    if not os.path.isdir(dirIn):
        msg = "directory " + dirIn + " does not exist!"
        tkMessageBox.showerror("Error", msg)
        sys.exit()


def errorExit(error):
    """Show error message in messagebox and then exit after userv presses OK"""
    tkMessageBox.showerror("Error", error)
    sys.exit()


def main_is_frozen():
    """Return True if application is frozen (Py2Exe), and False otherwise"""
    return (hasattr(sys, "frozen") or  # new py2exe
            hasattr(sys, "importers") or  # old py2exe
            imp.is_frozen("__main__"))  # tools/freeze


def get_main_dir():
    """Return application (installation) directory"""
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])


def findElementText(elt, elementPath):
    """Returns element text if it exists, errorExit if it doesn't exist"""
    elementText = elt.findtext(elementPath)
    if elementText is None:
        msg = 'no element found at ' + elementPath
        errorExit(msg)
    else:
        return elementText


def getConfiguration():
    """ Read configuration file, make all config variables available via
    config.py and check that all file paths / executables exist.
    This assumes an non-frozen script (no Py2Exe!)
    """

    # From where is this script executed?)
    rootPath = os.path.abspath(get_main_dir())
    # Locate Windows profile directory
    # userDir = os.path.expanduser('~') 
    userDir = os.environ['USERPROFILE']
    
    # Locate package directory
    packageDir = os.path.dirname(os.path.abspath(__file__))
    # Config directory
    configDirUser = os.path.join(userDir, 'iromlab')
    configFileUser = os.path.join(configDirUser, 'config.xml')
    # Tools directory
    toolsDirUser = os.path.join(packageDir, 'tools')

    # Check if user config file exists and exit if not
    if not os.path.isfile(configFileUser):
        print(configFileUser)
        msg = 'configuration file not found'
        errorExit(msg)

    # Read contents to bytes object
    try:
        fConfig = open(configFileUser, "rb")
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
    config.tempDir = findElementText(configElt, './config/tempDir')
    config.secondsToTimeout = findElementText(configElt, './config/secondsToTimeout')
    config.prefixBatch = findElementText(configElt, './config/prefixBatch')
    config.audioFormat = findElementText(configElt, './config/audioFormat')
    config.reportFormatString = findElementText(configElt, './config/reportFormatString')
    config.prebatchExe = findElementText(configElt, './config/prebatchExe')
    config.loadExe = findElementText(configElt, './config/loadExe')
    config.unloadExe = findElementText(configElt, './config/unloadExe')
    config.rejectExe = findElementText(configElt, './config/rejectExe')
    config.isoBusterExe = findElementText(configElt, './config/isoBusterExe')
    config.dBpowerampConsoleRipExe = findElementText(configElt, './config/dBpowerampConsoleRipExe')
    if findElementText(configElt, './config/enablePPNLookup') == "True":
        config.enablePPNLookup = True
    else:
        config.enablePPNLookup = False

    # Normalise all file paths
    config.rootDir = os.path.normpath(config.rootDir)
    config.tempDir = os.path.normpath(config.tempDir)
    config.prebatchExe = os.path.normpath(config.prebatchExe)
    config.loadExe = os.path.normpath(config.loadExe)
    config.unloadExe = os.path.normpath(config.unloadExe)
    config.rejectExe = os.path.normpath(config.rejectExe)
    config.isoBusterExe = os.path.normpath(config.isoBusterExe)
    config.dBpowerampConsoleRipExe = os.path.normpath(config.dBpowerampConsoleRipExe)

    # Paths to pre-packaged tools
    config.shntoolExe = os.path.join(toolsDirUser, 'shntool', 'shntool.exe')
    config.flacExe = os.path.join(toolsDirUser, 'flac', 'win64', 'flac.exe')
    config.cdInfoExe = os.path.join(toolsDirUser, 'libcdio', 'win64', 'cd-info.exe')

    # Check if all files and directories exist, and exit if not
    checkDirExists(config.rootDir)
    checkDirExists(config.tempDir)
    checkFileExists(config.prebatchExe)
    checkFileExists(config.loadExe)
    checkFileExists(config.unloadExe)
    checkFileExists(config.rejectExe)
    checkFileExists(config.isoBusterExe)
    checkFileExists(config.dBpowerampConsoleRipExe)
    checkFileExists(config.shntoolExe)
    checkFileExists(config.flacExe)
    checkFileExists(config.cdInfoExe)

    # Check that cdDriveLetter points to an existing optical drive
    resultGetDrives = cdinfo.getDrives()
    cdDrives = resultGetDrives["drives"]
    if config.cdDriveLetter not in cdDrives:
        msg = '"' + config.cdDriveLetter + '" is not a valid optical drive!'
        errorExit(msg)

    # Check that audioFormat is wav or flac
    if config.audioFormat not in ["wav", "flac"]:
        msg = '"' + config.audioFormat + '" is not a valid audio format (expected "wav" or "flac")!'
        errorExit(msg)


def main():
    """Main function"""

    root = tk.Tk()
    myCarrierEntry = carrierEntry(root)
    # This ensures application quits normally if user closes window
    root.protocol('WM_DELETE_WINDOW', myCarrierEntry.on_quit)
    t1 = threading.Thread(target=cdworker.cdWorker, args=[])
    t1.start()

    while True:
        try:
            root.update_idletasks()
            root.update()
            time.sleep(0.1)
        except KeyboardInterrupt:
            if config.finishedBatch:
                t1.join()
                handlers = myCarrierEntry.logger.handlers[:]
                for handler in handlers:
                    handler.close()
                    myCarrierEntry.logger.removeHandler(handler)
                # Notify user
                msg = 'Finished processing this batch'
                tkMessageBox.showinfo("Finished", msg)
                # Reset the GUI
                myCarrierEntry.reset_gui()
                # Start cdworker
                root.protocol('WM_DELETE_WINDOW', myCarrierEntry.on_quit)
                t1 = threading.Thread(target=cdworker.cdWorker, args=[])
                t1.start()
            elif config.quitFlag:
                # User pressed exit
                t1.join()
                handlers = myCarrierEntry.logger.handlers[:]
                for handler in handlers:
                    handler.close()
                    myCarrierEntry.logger.removeHandler(handler)
                msg = 'Quitting because user pressed Exit, click OK to exit'
                tkMessageBox.showinfo("Exit", msg)
                os._exit(0)

if __name__ == "__main__":
    main()
