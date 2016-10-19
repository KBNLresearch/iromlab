import win32api


drives = win32api.GetLogicalDriveStrings()
vName, nNo, mxCLen, flags, string   = win32api.GetVolumeInformation("I:")
print(vName, nNo, mxCLen, flags, string)
