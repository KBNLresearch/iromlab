#! /usr/bin/env python
"""Fetch MDO record for a PPN and write it to file"""

import os
import io
import logging
import xml.etree.ElementTree as ETree
from .kbapi import sru

def writeMDORecord(PPN, writeDirectory):
    """Write MDO record for a PPN to file"""

    fileOut = os.path.join(writeDirectory, "meta-kbmdo.xml")

    sruSearchString = '"PPN=' + str(PPN) + '"'
    response = sru.search(sruSearchString, "GGC")

    if not response:
        logging.error("No matching metadata record found in KB-MDO")
        success = False
    else:
        recordData = next(response.records).record_data
        recordAsString = ETree.tostring(recordData, encoding='UTF-8', method='xml')

        try:
            with io.open(fileOut, "wb") as fOut:
                fOut.write(recordAsString)
            fOut.close()
            success = True
        except IOError:
            logging.error("Could not write KB-MDO metadata to file")
            success = False

    return success