from isolyzer import isolyzer
import os
import sys
import codecs
import xml.etree.ElementTree as ET

#out = codecs.getwriter("UTF-8")(sys.stdout.buffer)

#dataTrackLSNStart = "021917"
dataTrackLSNStart = "0"
isoFileTemp = os.path.normpath("E:/testiromlab/kb-b1a145b6-2f4d-11e7-9b25-7446a0b42b9a/b6c70022-2f4d-11e7-a77d-7446a0b42b9a/disc.iso")
isoFileTemp = os.path.normpath("E:/testiromlab/test4/155658050/cd-rom/1/Handbook.iso")
isolyzerResult = isolyzer.processImage(isoFileTemp, dataTrackLSNStart)

for elem in isolyzerResult.iter():
    print(elem, elem.text)

#print(type(isolyzerResult))
#xmlOut = ET.tostring(isolyzerResult, 'unicode', 'xml')
#codec.write(xmlOut)
# Isolyzer status
isolyzerSuccess = isolyzerResult.find('statusInfo/success').text       
# Is ISO image smaller than expected (if True, this indicates the image may be truncated)
imageTruncated = isolyzerResult.find('tests/smallerThanExpected').text               
# Volume identifier from ISO's Primary Volume Descriptor 
volumeIdentifier = isolyzerResult.find('properties/primaryVolumeDescriptor/volumeIdentifier').text.strip()

#print(isolyzerSuccess)