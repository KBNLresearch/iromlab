#! /usr/bin/env python
"""Wrapper module for Isobuster"""

import os
import io
from isolyzer import isolyzer
from . import config
from . import shared


def extractData(writeDirectory, session, dataTrackLSNStart):
    """Extract data to ISO image using specified session number"""

    # Temporary name for ISO file; base name
    isoFileTemp = os.path.join(writeDirectory, "disc.iso")
    logFile = os.path.join(writeDirectory, "isobuster.log")
    reportFile = os.path.join(writeDirectory, "isobuster-report.xml")
    
    # Format string that defines DFXML output report
    reportFormatString = config.reportFormatString
    #reportFormatString = "{'DFXML (IsoBuster 4.1 version)'}{%UTF8}{%XML}{%GMT}{%FOLDERS}{%STREAMS}<%XMLHEADER><%BR><dfxml xmlns='http://www.forensicswiki.org/wiki/Category:Digital_Forensics_XML'<%BR> xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'<%BR> xmlns:dc='http://purl.org/dc/elements/1.1/'<%BR> xmlns:hfs='http://www.forensicswiki.org/wiki/HFS' version='1.0'><%BR><%BR> <metadata><%BR> <dc:type><%DEVICETYPE></dc:type><%BR> </metadata><%BR><%BR> <creator><%BR> <program><%APP></program><%BR> <version><%VERSION></version><%BR> <execution_environment><%BR> <start_time><%SYSTIMEDATE></start_time><!--GMT--><%BR> <os_version><%OS></os_version><%BR> <username><%USER></username><%BR> </execution_environment><%BR> </creator><%BR><%BR> <source><%BR> <device_model><%DEVICE></device_model><%BR> <image_filename><%DEVICEPATH></image_filename><%BR> <image_size><%DEVICEFILESIZE></image_size><%BR> <sectorsize><%DEVICEBLOCKSIZE></sectorsize><%BR> <devicesectors coding='base10'><%DEVICEBLOCKS></devicesectors><%BR> </source><%BR><%BR> <volume><%BR> <ftype_str><%TYPE></ftype_str><%BR> <partition_offset><%PARTITIONLBABYTESOFFSET></partition_offset>{%HEADER}{%FOLDER}<%BR> <fileobject><%BR> <filename><%RELPATH></filename><%BR> <name_type>d</name_type><%BR> <filesize><%BYTES></filesize><%BR> <alloc>1</alloc><%BR> <inode><%UID></inode><%BR> <mtime><%TIMEDATE></mtime><!--GMT--><%BR> <byte_runs><%EXTENTLOOP> </byte_runs><%BR> </fileobject>{%FILE}<%BR> <fileobject><%BR> <filename><%RELPATH></filename><%BR> <name_type>r</name_type><%BR> <filesize><%BYTES></filesize><%BR> <alloc>1</alloc><%BR> <inode><%UID></inode><%BR> <mtime><%TIMEDATE></mtime><!--GMT--><%BR> <hfs:HFStype_creator><%TYPE>/<%CREATOR></hfs:HFStype_creator><!--Only relevant if MAC File System--><%BR> <byte_runs><%EXTENTLOOP> </byte_runs><%BR> </fileobject>{%STREAM}<%BR> <fileobject><!--Stream or Resource Fork--><%BR> <filename><%RELPATH></filename><%BR> <name_type>-</name_type><%BR> <filesize><%BYTES></filesize><%BR> <alloc>1</alloc><%BR> <inode><%UID></inode><%BR> <mtime><%TIMEDATE></mtime><!--GMT--><%BR> <byte_runs><%EXTENTLOOP> </byte_runs><%BR> </fileobject>{%EXTENT} <byte_run img_offset='<%LBABYTEOFFSET>' len='<%BYTES>' />{%FOOTER} </volume><%BR><%BR> <runstats><%BR> <stop_time><%SYSTIMEDATE></stop_time><!--GMT--><%BR> <clock_seconds><%SYSTIMELAPSEDSEC></clock_seconds><%BR> </runstats><%BR><%BR></dfxml><%BR><!-- For more information: https://www.isobuster.com/reports -->"

    args = [config.isoBusterExe]
    args.append("".join(["/d:", config.cdDriveLetter, ":"]))
    args.append("".join(["/ei:", isoFileTemp]))
    args.append("/et:u")
    args.append("/ep:oea")
    args.append("/ep:npc")
    args.append("/c")
    args.append("/m")
    args.append("/nosplash")
    args.append("".join(["/s:", str(session)]))
    args.append("".join(["/l:", logFile]))
    args.append("".join(["/tree:all:", reportFile, '?', reportFormatString]))

    # Command line as string (used for logging purposes only)
    cmdStr = " ".join(args)

    status, out, err = shared.launchSubProcess(args)

    # Open and read log file
    with io.open(logFile, "r", encoding="cp1252") as fLog:
        log = fLog.read()
    fLog.close()

    # Rewrite as UTF-8
    with io.open(logFile, "w", encoding="utf-8") as fLog:
        fLog.write(log)
    fLog.close()

    # Run isolyzer to verify if ISO is complete and extract volume identifier text string
    try:
        isolyzerResult = isolyzer.processImage(isoFileTemp, dataTrackLSNStart)
        # Isolyzer status
        isolyzerSuccess = isolyzerResult.find('statusInfo/success').text
        # Is ISO image smaller than expected (if True, this indicates the image may be truncated)
        imageTruncated = isolyzerResult.find('tests/smallerThanExpected').text
        # Volume identifier from ISO's Primary Volume Descriptor
        # TODO: make this work for other fs types as well (UDF, HFS, HFS+)
        volumeIdentifier = isolyzerResult.find("fileSystems/fileSystem[@TYPE='ISO 9660']"
                                               "/primaryVolumeDescriptor/"
                                               "volumeIdentifier").text.strip()

    except IOError or AttributeError:
        volumeIdentifier = ''
        isolyzerSuccess = False
        imageTruncated = True

    if volumeIdentifier != '':
        # Rename ISO image using volumeIdentifier as a base name
        # Any spaces in volumeIdentifier are replaced with dashes
        isoFile = os.path.join(writeDirectory, volumeIdentifier.replace(' ', '-') + '.iso')
        os.rename(isoFileTemp, isoFile)

    # All results to dictionary
    dictOut = {}
    dictOut["cmdStr"] = cmdStr
    dictOut["status"] = status
    dictOut["stdout"] = out
    dictOut["stderr"] = err
    dictOut["log"] = log
    dictOut["volumeIdentifier"] = volumeIdentifier
    dictOut["isolyzerSuccess"] = isolyzerSuccess
    dictOut["imageTruncated"] = imageTruncated

    return dictOut
