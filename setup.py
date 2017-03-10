#!/usr/bin/env python

import codecs
import os
import re
import sys
import sysconfig

from setuptools import setup, find_packages

def read(*parts):
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as fobj:
        return fobj.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")
    
def get_reg(name,path):
    # Read variable from Windows Registry
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
    # Creates a Desktop shortcut to the installed software
    
    from win32com.client import Dispatch
        
    # Package name
    packageName = 'iromlab'

    # Scripts directory (location of launcher script)
    scriptsDir = sysconfig.get_path('scripts')

    # Target of shortcut
    target = os.path.join(scriptsDir, packageName + '.exe')

    # Name of link file
    linkName = packageName + '.lnk'

    # Read location of Windows desktop folder from registry
    regName = 'Desktop'
    regPath = r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
    desktopFolder = os.path.normpath(get_reg(regName,regPath))

    # Path to location of link file
    pathLink = os.path.join(desktopFolder, linkName)
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(pathLink)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = scriptsDir
    shortcut.IconLocation = target
    shortcut.save()
        
install_requires = [
    'requests',
    'setuptools',
    'wmi',
    'isolyzer',
    'lxml',
    'pypiwin32'
]

setup(name='iromlab',
      packages=find_packages(),
      version=find_version('iromlab', 'iromlab.pyw'),
      license='Apache License 2.0',
      install_requires=install_requires,
      platforms=['Windows'],
      description='Image and Rip Optical Media Like A Boss',
      long_description='Loader software for automated imaging of optical media with Nimbie disc robot ',
      author='Johan van der Knijff',
      author_email='johan.vanderknijff@kb.nl',
      maintainer='Johan van der Knijff',
      maintainer_email='johan.vanderknijff@kb.nl',
      url='https://github.com/KBNLresearch/iromlab',
      download_url='https://github.com/KBNLresearch/iromlab/archive/' + find_version('iromlab', 'iromlab.pyw') + '.tar.gz',
      package_data={'iromlab': ['*.*', 'conf/*.*', 'tools/*.*','tools/flac/*.*','tools/flac/win64/*.*','tools/flac/html/*.*','tools/flac/html/images/*.*','tools/flac/win32/*.*','tools/shntool/*.*','tools/shntool/doc/*.*', 'tools/libcdio/*.*','tools/libcdio/win64/*.*']},
      zip_safe=False,
      entry_points={'gui_scripts': [
        'iromlab = iromlab.iromlab:main',
      ]},
      classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ]
    )

if sys.argv[1] == 'install' and sys.platform == 'win32':
    post_install()

