#!/usr/bin/python3

#from Tkinter import *
import Tkinter as tk
textFields = [
    'Catalog ID (PPN)', 
    'Volume number', 
    'Number of volumes'
]

carrierTypes = [
    ('cd-audio',1),
    ('cd-rom',2),
    ('dvd-rom',3),
    ('dvd-video',4)
]

def getValues(entries,v):
    for entry in entries:
        print(entry[1].get())
    
    print(v.get())
        
def makeform(root, fields):
    entries = []
    for field in textFields:
        row = tk.Frame(root)
        lab = tk.Label(row, width=17, text=field, anchor='w')
        userValue = tk.StringVar()
        userValue.set('')
        ent = tk.Entry(row, textvariable=userValue)
        row.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
        entries.append((field, userValue))
    
    # Select carrier type
    v = tk.IntVar()
    v.set(1)
    
    row = tk.Frame(root)
    lab = tk.Label(row, width=17, text='Select carrier type:', anchor='w')
    row.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
    lab.pack(side=tk.LEFT)
    
    for carrierType, val in carrierTypes:
        row = tk.Frame(root)
        cb = tk.Radiobutton(row, text=carrierType, variable=v, value=val).grid(row=1, sticky=tk.W)
        row.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)
    
    return entries, v
  
if __name__ == '__main__':
    root = tk.Tk()
    root.title('Enter carrier details')
    ents, v = makeform(root, textFields)  
    root.bind('<Return>')   
    b1 = tk.Button(root, text='Show',
        command= lambda: getValues(ents,v))
    b1.pack(side=tk.LEFT, padx=5, pady=5)
    b2 = tk.Button(root, text='Quit', command=root.quit)
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    root.mainloop()