"""
Adapted from: http://www.datadependence.com/2016/04/how-to-build-gui-in-python-3/
"""
import sys
import os
import time
import threading
import shared
import glob
import config

try:
    import tkinter as tk #Python 3.x
    from tkinter import ttk as ttk
    import filedialog as tkFileDialog
except ImportError:
    import Tkinter as tk # Python 2.x
    import ttk as ttk
    import tkFileDialog

import tkMessageBox
from kbapi import sru

#global batchFolder
#batchFolder = ''
#workspace = 'E:/workspace'

def workerTest():

    preBatch = True

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
    
class carrierEntry(tk.Frame):
    
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.init_gui()
        self.jobsFolder = ''
         
    def on_quit(self):
        # Wait until the disc that is currently being pocessed has 
        # finished, and quit (batch can be resumed by opening it in the File dialog)
        config.quitFlag = True
        quit()
    
    def on_create(self):
        # Create new batch
        
        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = 'E:\\'
        options['mustexist'] = False
        options['parent'] = root
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
             
    def on_open(self):
        # Open existing batch
        
        # defining options for opening a directory
        self.dir_opt = options = {}
        options['initialdir'] = 'E:\\'
        options['mustexist'] = True
        options['parent'] = root
        options['title'] = 'Select batch directory'
        config.batchFolder = tkFileDialog.askdirectory(**self.dir_opt)
        config.jobsFolder = os.path.join(config.batchFolder, 'jobs')
        
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
        
        if representsInt(volumeNo) == False:
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
 
        self.grid(column=0, row=0, sticky='nsew')
        
        self.menubar = tk.Menu(self.root)
 
        self.menu_file = tk.Menu(self.menubar)
        self.menu_file.add_command(label='New batch ...', command=self.on_create)
        self.menu_file.add_command(label='Open batch ...', command=self.on_open)
        self.menu_file.add_command(label='Finalise batch ...', command=self.on_finalise)
        self.menu_file.add_command(label='Exit', command=self.on_quit)

        self.menu_edit = tk.Menu(self.menubar)

        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_edit, label='Edit')

        self.root.config(menu=self.menubar)
 
        tk.Label(self, text='Enter carrier details').grid(column=0, row=0,
                columnspan=4)
       
        ttk.Separator(self, orient='horizontal').grid(column=0,
                row=1, columnspan=4, sticky='ew')
                
        # Catalog ID        
        tk.Label(self, text='PPN').grid(column=0, row=2,
                sticky='w')
        self.catid_entry = tk.Entry(self, width=12)
        self.catid_entry.grid(column=2, row = 2)

        # Volume number
        tk.Label(self, text='Volume number').grid(column=0, row=3,
                sticky='w')
        self.volumeNo_entry = tk.Entry(self, width=5)
        self.volumeNo_entry.grid(column=2, row=3)

        # Number of volumes
        tk.Label(self, text='Number of volumes').grid(column=0, row=4,
                sticky='w')
        self.noVolumes_entry = tk.Entry(self, width=5)
        self.noVolumes_entry.grid(column=2, row=4)
 
        # Carrier type (radio button select)
        self.v = tk.IntVar()
        self.v.set(1)
        
        tk.Label(self, text='Carrier type').grid(column=0, row=5,
                sticky='w', columnspan=4)
                
        rowValue = 5
        
        for carrierType in self.carrierTypes:
            self.rb = tk.Radiobutton(self, text=carrierType[0], variable=self.v, value=carrierType[1]).grid(column=2, row=rowValue, 
            sticky='w')
            rowValue += 1
        
        self.submit_button = tk.Button(self, text='Submit',
                command=self.submit)
        self.submit_button.grid(column=0, row=11,  columnspan=4)
                
        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)
 
if __name__ == '__main__':

    root = tk.Tk()
    carrierEntry(root)
    
    t1 = threading.Thread(target=workerTest, args=[])
    t1.start()
    root.mainloop()
    t1.join()
