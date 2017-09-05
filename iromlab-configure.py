#!/usr/bin/env python
"""Post-install / configuration script for Iromlab"""

import os
import sys
import site
import sysconfig
from shutil import copyfile
from shutil import copytree
from win32com.client import Dispatch


def errorExit(msg):
    """Send error message to stderr and exit"""
    msgString = ("Error: " + msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()


def get_reg(name, path):
    """Read variable from Windows Registry"""
    import winreg
    # From http://stackoverflow.com/a/35286642
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                                      winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, name)
        winreg.CloseKey(registry_key)
        return value
    except WindowsError:
        return None


def post_install():
    """Install config file + pre-packaged tools to user dir +
    Create a Desktop shortcut to the installed software
    """

    # Package name
    packageName = 'iromlab'

    # Part 1: install config file

    # Locate Windows user directory
    userDir = os.path.expanduser('~')
    # Config directory
    configDirUser = os.path.join(userDir, packageName)

    # Create config directory if it doesn't exist
    if not os.path.isdir(configDirUser):
        try:
            os.makedirs(configDirUser)
        except IOError:
            msg = 'could not create configuration directory'
            errorExit(msg)

    # Config file name
    configFileUser = os.path.join(configDirUser, 'config.xml')

    if not os.path.isfile(configFileUser):
        # No config file in user dir, so copy it from location in package. Location
        # is /iromlab/conf/config.xml in 'site-packages' directory (if installed with pip)

        # Locate site-packages dir (this returns multiple entries)
        sitePackageDirs = site.getsitepackages()

        # Assumptions: site package dir is called 'site-packages' and is unique (?)
        for directory in sitePackageDirs:
            if 'site-packages' in directory:
                sitePackageDir = directory

        # Construct path to config file
        configFilePackage = os.path.join(sitePackageDir, packageName, 'conf', 'config.xml')

        if os.path.isfile(configFilePackage):
            try:
                copyfile(configFilePackage, configFileUser)
            except IOError:
                msg = 'could not copy configuration file to ' + configFileUser
                errorExit(msg)
        # This should never happen but who knows ...
        else:
            msg = 'no configuration file found in package'
            errorExit(msg)

    # Part 2: create Desktop shortcut

    # Scripts directory (location of launcher script)
    scriptsDir = sysconfig.get_path('scripts')

    # Target of shortcut
    target = os.path.join(scriptsDir, packageName + '.exe')

    # Name of link file
    linkName = packageName + '.lnk'

    # Read location of Windows desktop folder from registry
    regName = 'Desktop'
    regPath = r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
    desktopFolder = os.path.normpath(get_reg(regName, regPath))

    # Path to location of link file
    pathLink = os.path.join(desktopFolder, linkName)
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(pathLink)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = scriptsDir
    shortcut.IconLocation = target
    shortcut.save()

def main():
    """Main function"""
    post_install()

if __name__ == "__main__":
    main()
