#! /usr/bin/env python

from .kbapi import sru

def main():
    catid = "159281539"

    # Lookup catalog identifier
    sruSearchString = '"PPN=' + str(catid) + '"'
    sruSearchString = "OaiPmhIdentifier=%22GGC:AC:" + str(catid) + "%22&recordSchema=dcx+index&maximumRecords=10"
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


if __name__ == "__main__":
    main()