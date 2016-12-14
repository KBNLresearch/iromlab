import sys
import os
import isolyzer

isoFile = 'E:/nimbieTest/crap02/8d9f05ae-adaf-11e6-80e8-00237d497a29/data/disc.iso'
isolyzerResult = isolyzer.processImage(isoFile)
volumeIdentifier = isolyzerResult.findtext('properties/primaryVolumeDescriptor/volumeIdentifier')
print(volumeIdentifier)
