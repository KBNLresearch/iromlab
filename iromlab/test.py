import tkinter as tk
from tkinter import ttk

root = tk.Tk()

tree = ttk.Treeview(root)
tree["columns"]=("one","two", "three")
tree.column("one", width=100 )
tree.column("two", width=100)
tree.column("three", width=100)
tree.heading("one", text="Serial No.")
tree.heading("two", text="PPN")
tree.heading("three", text="Title")

tree.insert("" , 0,    text="Line 1", values=("1A","1b"))

id2 = tree.insert("", 1, "dir2", text="Dir 2")
tree.insert(id2, "end", "dir 2", text="sub dir 2", values=("2A","2B"))
tree.pack()

tk.mainloop()