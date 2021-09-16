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
import glob
import xml.etree.ElementTree as ETree
import threading
import uuid
import logging
import json
import queue
import tkinter as tk
from tkinter import filedialog as tkFileDialog
from tkinter import scrolledtext as ScrolledText
from tkinter import messagebox as tkMessageBox
from tkinter import ttk
from . import config
from .kbapi import sru
from .socketserver import server
from . import cdworker
from . import cdinfo


__version__ = '1.0.8'
config.version = __version__

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
        self.carrierNumber = 0
        self.build_gui()

    def on_quit(self, event=None):
        """Wait until the disc that is currently being pocessed has
        finished, and quit (batch can be resumed by opening it in the File dialog)
        """
        config.quitFlag = True
        self.bExit.config(state='disabled')
        self.bFinalise.config(state='disabled')
        if config.batchIsOpen:
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
            logging.info(''.join(['batchFolder set to ', config.batchFolder]))

            # Update state of buttons / widgets
            self.bNew.config(state='disabled')
            self.bOpen.config(state='disabled')
            self.bFinalise.config(state='normal')
            if config.enablePPNLookup:
                self.catid_entry.config(state='normal')
                self.usepreviousPPN_button.config(state='normal')
            else:
                self.title_entry.config(state='normal')
                self.usepreviousTitle_button.config(state='normal')
            self.volumeNo_entry.config(state='normal')
            self.volumeNo_entry.delete(0, tk.END)
            self.volumeNo_entry.insert(tk.END, "1")
            self.submit_button.config(state='normal')

            # Flag that is True if batch is open
            config.batchIsOpen = True
            # Set readyToStart flag to True, except if startOnFinalize flag is activated,
            # in which case readyToStart is set to True on finalisation
            if not config.startOnFinalize:
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
                    # Import info on jobs in queue to the treeview widget

                    # Get directory listing of job files sorted by creation time
                    jobFiles = list(filter(os.path.isfile, glob.glob(config.jobsFolder + '/*')))
                    jobFiles.sort(key=lambda x: os.path.getctime(x))
                    jobCount = 1

                    for job in  jobFiles:
                         # Open job file, read contents to list
                        fj = open(job, "r", encoding="utf-8")
                        fjCSV = csv.reader(fj)
                        jobList = next(fjCSV)
                        fj.close()

                        if jobList[0] != 'EOB':
                            PPN = jobList[1]
                            title = jobList[2]
                            volumeNo = jobList[3]

                            # Add PPN/Title + Volume number to treeview widget
                            self.tv.insert('', 0, text=str(jobCount), values=(PPN, title, volumeNo))
                            jobCount += 1

                    # Update state of buttons /widgets, taking into account whether batch was
                    # finalized by user
                    self.bNew.config(state='disabled')
                    self.bOpen.config(state='disabled')
                    if os.path.isfile(os.path.join(config.jobsFolder, 'eob.txt')):
                        self.bFinalise.config(state='disabled')
                        self.submit_button.config(state='disabled')
                    else:
                        self.bFinalise.config(state='normal')
                        self.submit_button.config(state='normal')
                    if config.enablePPNLookup:
                        self.catid_entry.config(state='normal')
                        self.usepreviousPPN_button.config(state='normal')
                    else:
                        self.title_entry.config(state='normal')
                        self.usepreviousTitle_button.config(state='normal')
                    self.volumeNo_entry.config(state='normal')
                    self.volumeNo_entry.delete(0, tk.END)
                    self.volumeNo_entry.insert(tk.END, "1")

                    # Flag that is True if batch is open
                    config.batchIsOpen = True
                    # Set readyToStart flag to True, except if startOnFinalize flag is activated,
                    # in which case readyToStart is set to True on finalisation
                    if not config.startOnFinalize:
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
            if config.enablePPNLookup:
                self.catid_entry.config(state='disabled')
                self.usepreviousPPN_button.config(state='disabled')
            else:
                self.title_entry.config(state='disabled')
                self.usepreviousTitle_button.config(state='disabled')
            self.volumeNo_entry.delete(0, tk.END)
            self.volumeNo_entry.config(state='disabled')
            
            # If the startOnFinalize option was activated, set readyToStart flag to True
            if config.startOnFinalize:
                config.readyToStart = True

    def on_usepreviousPPN(self, event=None):
        """Add previously entered PPN to entry field"""
        if self.catidOld == "":
            msg = "Previous PPN is not defined"
            tkMessageBox.showerror("PPN not defined", msg)
        else:
            self.catid_entry.delete(0, tk.END)
            self.catid_entry.insert(tk.END, self.catidOld)
            if self.volumeNoOld != "":
                # Increase volume number value
                volumeNoNew = str(int(self.volumeNoOld) + 1)
                self.volumeNo_entry.delete(0, tk.END)
                self.volumeNo_entry.insert(tk.END, volumeNoNew)

    def on_usepreviousTitle(self, event=None):
        """Add previously entered title to title field"""
        if self.titleOld == "":
            msg = "Previous title is not defined"
            tkMessageBox.showerror("Tile not defined", msg)
        else:
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(tk.END, self.titleOld)
            if self.volumeNoOld != "":
                volumeNoNew = str(int(self.volumeNoOld) + 1)
                self.volumeNo_entry.delete(0, tk.END)
                self.volumeNo_entry.insert(tk.END, volumeNoNew)

    def on_submit(self, event=None):
        """Process one record and add it to the queue after user pressed submit button"""

        self.carrierNumber += 1

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

        if config.enablePPNLookup:
            # Check for empty string
            if str(catid) == '':
                noGGCRecords = 0
            else:
                # Lookup catalog identifier
                sruSearchString = 'OaiPmhIdentifier="GGC:AC:' + str(catid) + '"'
                response = sru.search(sruSearchString, "GGC")

                if not response:
                    noGGCRecords = 0
                else:
                    noGGCRecords = response.sru.nr_of_records
        else:
            noGGCRecords = 1

        if not config.batchIsOpen:
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

                fJob = open(jobFile, "w", encoding="utf-8")

                # Create CSV writer object
                jobCSV = csv.writer(fJob, lineterminator='\n')

                # Row items to list
                rowItems = ([jobID, catid, title, volumeNo])

                # Write row to job and close file
                jobCSV.writerow(rowItems)
                fJob.close()

                # Display PPN/Title + Volume number in treeview widget
                self.tv.insert('', 0, text=str(self.carrierNumber), values=(catid, title, volumeNo))

                # Reset entry fields and set focus on PPN / Title field
                if config.enablePPNLookup:
                    self.catid_entry.delete(0, tk.END)
                    self.catid_entry.focus_set()
                else:
                    self.title_entry.delete(0, tk.END)
                    self.title_entry.focus_set()
                self.volumeNo_entry.delete(0, tk.END)
                self.volumeNo_entry.insert(tk.END, "1")

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
        
        self.root.title('iromlab v.' + config.version)
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

        ttk.Separator(self, orient='horizontal').grid(column=0, row=2, columnspan=4, sticky='ew')

        # Entry elements for each carrier

        if config.enablePPNLookup:
            # Catalog ID (PPN)
            tk.Label(self, text='PPN').grid(column=0, row=3, sticky='w')
            self.catid_entry = tk.Entry(self, width=20, state='disabled')

            # Pressing this button adds previously entered PPN to entry field
            self.usepreviousPPN_button = tk.Button(self,
                               text='Use previous',
                               height=1,
                               width=2,
                               underline=0,
                               state='disabled',
                               command=self.on_usepreviousPPN)
            self.usepreviousPPN_button.grid(column=2, row=3, sticky='ew')

            self.catid_entry.grid(column=1, row=3, sticky='w')
        else:
            # PPN lookup disabled, so present Title entry field
            tk.Label(self, text='Title').grid(column=0, row=3, sticky='w')
            self.title_entry = tk.Entry(self, width=45, state='disabled')

            # Pressing this button adds previously entered title to entry field
            self.usepreviousTitle_button = tk.Button(self,
                               text='Use previous',
                               height=1,
                               width=2,
                               underline=0,
                               state='disabled',
                               command=self.on_usepreviousTitle)
            self.usepreviousTitle_button.grid(column=3, row=3, sticky='ew')
            self.title_entry.grid(column=1, row=3, sticky='w', columnspan=3)

        # Volume number
        tk.Label(self, text='Volume number').grid(column=0, row=4, sticky='w')
        self.volumeNo_entry = tk.Entry(self, width=5, state='disabled')
        
        self.volumeNo_entry.grid(column=1, row=4, sticky='w')

        ttk.Separator(self, orient='horizontal').grid(column=0, row=5, columnspan=4, sticky='ew')

        self.submit_button = tk.Button(self,
                                       text='Submit',
                                       height=2,
                                       width=4,
                                       underline=0,
                                       state='disabled',
                                       command=self.on_submit)
        self.submit_button.grid(column=1, row=6, sticky='ew')

        ttk.Separator(self, orient='horizontal').grid(column=0, row=7, columnspan=4, sticky='ew')

        # Treeview widget displays info on entered carriers
        self.tv = ttk.Treeview(self, height=10,
                               columns=('PPN', 'Title', 'VolumeNo'))
        self.tv.heading('#0', text='Queue number')
        self.tv.heading('#1', text='PPN')
        self.tv.heading('#2', text='Title')
        self.tv.heading('#3', text='Volume number')
        self.tv.column('#0', stretch=tk.YES, width=5)
        self.tv.column('#1', stretch=tk.YES, width=10)
        self.tv.column('#2', stretch=tk.YES, width=250)
        self.tv.column('#3', stretch=tk.YES, width=5)
        self.tv.grid(column=0, row=8, sticky='ew', columnspan=4)

        # ScrolledText widget displays logging info
        self.st = ScrolledText.ScrolledText(self, state='disabled', height=15)
        self.st.configure(font='TkFixedFont')
        self.st.grid(column=0, row=10, sticky='ew', columnspan=4)

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
        # Reset carrierNumber
        self.carrierNumber = 0
        # Clear items in treeview widget
        tvItems = self.tv.get_children()
        for item in tvItems:
           self.tv.delete(item)
        # Clear contents of ScrolledText widget
        # Only works if state is 'normal'
        self.st.config(state='normal')
        self.st.delete(1.0, tk.END)
        self.st.config(state='disabled')
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

        # Update state of buttons / widgets
        self.bNew.config(state='normal')
        self.bOpen.config(state='normal')
        self.bFinalise.config(state='disabled')
        self.bExit.config(state='normal')
        self.submit_button.config(state='disabled')
        if config.enablePPNLookup:
            self.catid_entry.config(state='disabled')
            self.usepreviousPPN_button.config(state='disabled')
        else:
            self.title_entry.config(state='disabled')
            self.usepreviousTitle_button.config(state='disabled')
        self.volumeNo_entry.config(state='disabled')

    def handleSocketRequests(self, q):
        """ Update contents of PPN and Title widgets on incoming requests from socket interface
        """
        try:
            message = q.get_nowait()
            if config.enablePPNLookup:
                try:
                    catid = message
                    self.catid_entry.delete(0, tk.END)
                    self.catid_entry.insert(tk.END, catid)
                    if catid == self.catidOld and catid != "":
                        # Increase volume number value if existing catid
                        volumeNoNew = str(int(self.volumeNoOld) + 1)
                        self.volumeNo_entry.delete(0, tk.END)
                        self.volumeNo_entry.insert(tk.END, volumeNoNew)
                except:
                    # TODO: catch more specific errors here?
                    pass
            else:
                try:
                    title = message
                    self.title_entry.delete(0, tk.END)
                    self.title_entry.insert(tk.END, title)
                    if title == self.titleOld and title != "":
                        # Increase volume number value if existing catid
                        volumeNoNew = str(int(self.volumeNoOld) + 1)
                        self.volumeNo_entry.delete(0, tk.END)
                        self.volumeNo_entry.insert(tk.END, volumeNoNew)
                except:
                    # TODO: catch more specific errors here?
                    pass
        except queue.Empty:
            pass

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

    # Locate Windows profile directory
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
 
    # For below configuration variables, use default value if value cannot be
    # read from config file (this ensures v1 will work with old config files)
    try:
        config.socketHost = findElementText(configElt, './config/socketHost')
    except:
        pass
    try:
        config.socketPort = findElementText(configElt, './config/socketPort')
    except:
        pass
    try:
        if findElementText(configElt, './config/enablePPNLookup') == "True":
            config.enablePPNLookup = True
        else:
            config.enablePPNLookup = False
    except:
        pass
    try:
        if findElementText(configElt, './config/startOnFinalize') == "True":
            config.startOnFinalize = True
        else:
            config.startOnFinalize = False
    except:
        pass
    try:
        if findElementText(configElt, './config/enableSocketAPI') == "True":
            config.enableSocketAPI = True
        else:
            config.enableSocketAPI = False
    except:
        pass

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
    config.version = __version__
    root = tk.Tk()
    myCarrierEntry = carrierEntry(root)
    # This ensures application quits normally if user closes window
    root.protocol('WM_DELETE_WINDOW', myCarrierEntry.on_quit)
    # Start worker as separate thread
    t1 = threading.Thread(target=cdworker.cdWorker, args=[])
    t1.start()
    # Start socket API as separate thread
    if config.enableSocketAPI:
        q = queue.Queue()
        myServer = server()
        t2 = threading.Thread(target=server.start,
                              args=[myServer, config.socketHost, config.socketPort, q])
        t2.start()

    while True:
        try:
            if config.enableSocketAPI:
                myCarrierEntry.handleSocketRequests(q)
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
                if config.enableSocketAPI:
                    t2.join()
                handlers = myCarrierEntry.logger.handlers[:]
                for handler in handlers:
                    handler.close()
                    myCarrierEntry.logger.removeHandler(handler)
                msg = 'Quitting because user pressed Exit, click OK to exit'
                tkMessageBox.showinfo("Exit", msg)
                os._exit(0)

if __name__ == "__main__":
    main()
