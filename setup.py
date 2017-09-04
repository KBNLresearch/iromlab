#!/usr/bin/env python
"""Setup script for Iromlab"""

import codecs
import os
import site
from shutil import copyfile
from shutil import copytree
import re
import sys
import sysconfig
from setuptools import setup, find_packages


def errorExit(msg):
    """Send error message to stderr and exit"""
    msgString = ("Error: " + msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()


def read(*parts):
    """Read file and return contents"""
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as fobj:
        return fobj.read()


def find_version(*file_paths):
    """Return version number from main module"""
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


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

    from win32com.client import Dispatch

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

    # Part 2: install tools

    # Tools directory
    toolsDirUser = os.path.join(configDirUser, 'tools')

    if not os.path.isdir(toolsDirUser):
        # No tools directory in user dir, so copy it from location in source or package. Location is
        # /iromlab/conf/tools in 'site-packages' directory (if installed with pip)

        # Locate site-packages dir (this returns multiple entries)
        sitePackageDirs = site.getsitepackages()

        # Assumptions: site package dir is called 'site-packages' and is unique (?)
        for directory in sitePackageDirs:
            if 'site-packages'in directory:
                sitePackageDir = directory

        # Construct path to tools dir
        toolsDirPackage = os.path.join(sitePackageDir, 'iromlab', 'tools')

        # If package tools dir exists, copy it to the user directory
        if os.path.isdir(toolsDirPackage):
            try:
                copytree(toolsDirPackage, toolsDirUser)
            except IOError:
                msg = 'could not copy tools directory to ' + toolsDirUser
                errorExit(msg)
        # This should never happen but who knows ...
        else:
            msg = 'no tools directory found in package'
            errorExit(msg)

    # Part 3: create Desktop shortcut

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


INSTALL_REQUIRES = [
    'requests',
    'setuptools',
    'wmi',
    'isolyzer>=1',
    'lxml',
    'pypiwin32'
]
PYTHON_REQUIRES = '>=3.2'

setup(name='iromlab',
      packages=find_packages(),
      version=find_version('iromlab', 'iromlab.pyw'),
      license='Apache License 2.0',
      install_requires=INSTALL_REQUIRES,
      python_requires=PYTHON_REQUIRES,
      platforms=['Windows'],
      description='Image and Rip Optical Media Like A Boss',
      long_description='Loader software for automated imaging of optical media with Nimbie \
        disc robot ',
      author='Johan van der Knijff',
      author_email='johan.vanderknijff@kb.nl',
      maintainer='Johan van der Knijff',
      maintainer_email='johan.vanderknijff@kb.nl',
      url='https://github.com/KBNLresearch/iromlab',
      download_url=('https://github.com/KBNLresearch/iromlab/archive/' +
                    find_version('iromlab', 'iromlab.pyw') + '.tar.gz'),
      package_data={'iromlab': ['*.*', 'conf/*.*',
                                'tools/*.*', 'tools/flac/*.*',
                                'tools/flac/win64/*.*',
                                'tools/flac/html/*.*',
                                'tools/flac/html/images/*.*',
                                'tools/flac/win32/*.*',
                                'tools/shntool/*.*',
                                'tools/shntool/doc/*.*',
                                'tools/libcdio/*.*',
                                'tools/libcdio/win64/*.*']},
      zip_safe=False,
      entry_points={'gui_scripts': [
          'iromlab = iromlab.iromlab:main',
      ]},
      classifiers=[
          'Environment :: Console',
          'Programming Language :: Python :: 3',]
     )

if sys.argv[1] == 'install' and sys.platform == 'win32':
    post_install()
