from kbapi import sru

PPN = "26732653X"
#PPN = "18594650X"
catid = PPN

# Lookup catalog identifier
sruSearchString = '"PPN=' + str(catid) + '"'
response = sru.search(sruSearchString,"GGC")

if response == False:
    noGGCRecords = 0
else:
    noGGCRecords = response.sru.nr_of_records
    
if noGGCRecords == 0:
    # No matching record found
    msg = ("Search for PPN=" + str(catid) + " returned " + \
        "no matching record in catalog!")
    print(msg)
else:
    # Matching record found. Display title and ask for confirmation
    record = next(response.records)
    titlesMain = record.titlesMain
    titles = record.titles
        
    print(len(titles))
    print(len(titlesMain))
    
    if titlesMain == []:
        print(titles[0])
    else:
        print(titlesMain[0])