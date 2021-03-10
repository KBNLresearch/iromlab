#! /usr/bin/env python

import io
import xml.etree.ElementTree as ETree
from .kbapi import sru

def main():
    """
    Script for testing SRU interface outside Iromlab
    (not used by main Iromlab application)
    """
    catid = "184556155"

    # Lookup catalog identifier
    #sruSearchString = '"PPN=' + str(catid) + '"'
    sruSearchString = 'OaiPmhIdentifier="GGC:AC:' + str(catid) + '"'
    print(sruSearchString)
    response = sru.search(sruSearchString, "GGC")

    if not response:
        noGGCRecords = 0
    else:
        noGGCRecords = response.sru.nr_of_records

    if noGGCRecords == 0:
        # No matching record found
        msg = ("Search for PPN=" + str(catid) + " returned " +
                "no matching record in catalog!")
        print("PPN not found", msg)
    else:
        record = next(response.records)

        # Title can be in either in:
        # 1. title element
        # 2. title element with maintitle attribute
        # 3. title element with intermediatetitle attribute (3 in combination with 2)

        titlesMain = record.titlesMain
        titlesIntermediate = record.titlesIntermediate
        titles = record.titles

        if titlesMain != []:
            title = titlesMain[0]
            if titlesIntermediate != []:
                title = title + ", " + titlesIntermediate[0]
        else:
            title = titles[0]
        
        print("Title: " + title)

        # Write XML
        recordData = record.record_data
        recordAsString = ETree.tostring(recordData, encoding='UTF-8', method='xml')
        try:
            with io.open("meta-kbmdo.xml", "wb") as fOut:
                fOut.write(recordAsString)
            fOut.close()
        except IOError:
            print("Could not write KB-MDO metadata to file")



if __name__ == "__main__":
    main()