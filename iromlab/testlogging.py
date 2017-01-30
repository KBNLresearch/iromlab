#! /usr/bin/env python
import time
import threading
import logging
import ScrolledText
try:
    import tkinter as tk #Python 3.x
except ImportError:
    import Tkinter as tk # Python 2.x

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

class myGUI(tk.Frame):

    # This class defines the graphical user interface 
    
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.root = parent
        self.build_gui()
        
    def build_gui(self):
                        
        # Build GUI
        self.root.title('TEST')
        self.root.option_add('*tearOff', 'FALSE')
        self.grid(column=0, row=0, sticky='ew')
        self.grid_columnconfigure(0, weight=1, uniform='a')
        self.grid_columnconfigure(1, weight=1, uniform='a')
        self.grid_columnconfigure(2, weight=1, uniform='a')
        self.grid_columnconfigure(3, weight=1, uniform='a')
        
        # Add text widget to display logging info
        st = ScrolledText.ScrolledText(self, state='disabled')
        st.configure(font='TkFixedFont')
        st.grid(column=0, row=1, sticky='w', columnspan=4)

        # Create textLogger
        text_handler = TextHandler(st)
        
        # Logging configuration
        logging.basicConfig(filename='test.log',
            level=logging.DEBUG, 
            format='%(asctime)s - %(levelname)s - %(message)s')        
        
        # Add the handler to logger
        logger = logging.getLogger()
              
        logger.addHandler(text_handler)

        # Log some messages
        logger.debug('debug message')
        logger.info('info message')
        logger.warn('warn message')
        logger.error('error message')
        logger.critical('critical message')
        
        
def worker():

    # Skeleton worker function
    
    while True:
        time.sleep(2)
        msg = 'Waking up!'
        print(msg)
        logging.error(msg) 
        
def main():
    
    # Make logger variable global
    global logger
    
    root = tk.Tk()
    myGUI(root)
    
    t1 = threading.Thread(target=worker, args=[])
    t1.start()
        
    root.mainloop()
    t1.join()
        
main()