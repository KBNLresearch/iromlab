#! /usr/bin/env python
"""
Quick and dirty module for writing entire MDO record for a PPN to file
using SRU query. Code based on kbapi.sru.py
"""

import os
import io
import requests
import urllib

def writeMDORecord(PPN, writeDirectory):
    """Write MDO record for a PPN to file"""

    fileOut = os.path.join(writeDirectory, "meta-kbmdo.xml")
    sruSearchString = '"PPN=' + PPN + '"'

    SRU_BASEURL = 'http://jsru.kb.nl/sru/sru'
    SRU_BASEURL += '?version=1.2&maximumRecords=%i'
    SRU_BASEURL += '&operation=searchRetrieve'
    SRU_BASEURL += '&startRecord=%i'
    SRU_BASEURL += '&recordSchema=%s'
    SRU_BASEURL += '&x-collection=%s&query=%s'

    maximumrecords = 1
    startrecord = 1
    recordschema = 'dcx'
    collection = 'GGC'

    query = urllib.parse.quote_plus(sruSearchString)

    url = SRU_BASEURL % (maximumrecords, startrecord,
                         recordschema, collection, query)
    r = requests.get(url)

    if r.status_code != 200:
        # Status code: must be 200, otherwise an error occurred
        wroteMDORecord = False
    else:
        record_data = r.content.decode("utf-8") 

        try:
            with io.open(fileOut, "w", encoding="utf-8") as fOut:
                fOut.write(str(record_data))
            fOut.close()
            wroteMDORecord = True
        except IOError:
            wroteMDORecord = False

    return wroteMDORecord
