import win32api
import wmi
import time

def testDrive(letter):
    """
    Tests a given drive letter to see if the drive is question is ready for 
    access. This is to handle things like floppy drives and USB card readers
    which have to have physical media inserted in order to be accessed.
    Returns true if the drive is ready, false if not.
    Source: http://stackoverflow.com/a/1020363
    """
    returnValue = False
    # This prevents Windows from showing an error to the user, and allows python 
    # to handle the exception on its own.
    oldError = win32api.SetErrorMode(1) #note that SEM_FAILCRITICALERRORS = 1
    try:
    	freeSpace = win32api.GetDiskFreeSpaceEx(letter)
    except:
    	returnValue = False
    else:
    	returnValue = True
    # restore the Windows error handling state to whatever it was before we
    # started messing with it:
    win32api.SetErrorMode(oldError)
    return(returnValue)

def mediumLoaded(driveName):
    # Returns True if medium is loaded, False if not
    c = wmi.WMI()
    result = False
    for cdrom in c.Win32_CDROMDrive():
        if cdrom.Drive == driveName:
            print(cdrom)
            result = cdrom.MediaLoaded
        return(result)
        
def main():
    driveLetter = "J"
    
    loaded = False
    
    # Reject if no CD is found after 20 s
    timeout = time.time() + 1
    while loaded == False and time.time() < timeout:
        # TODO: define timeout value to prevent infinite loop in case of unreadable disc
        time.sleep(2)
        loaded = mediumLoaded(driveLetter + ":")
       
    print("medium loaded: " + str(loaded))

main()
