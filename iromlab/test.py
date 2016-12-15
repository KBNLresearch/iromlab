import sys
import os
import isolyzer

dirDisc = 'E:\nimbieTest\crap03\a21ad540-c2dc-11e6-a89d-00237d497a29'
batchFolder = 'E:\nimbieTest\crap03'
dirDiscRel = os.path.relpath(dirDisc, os.path.commonprefix([dirDisc, batchFolder]))[1:] 

print(dirDiscRel)
