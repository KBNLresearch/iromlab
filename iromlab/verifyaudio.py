#! /usr/bin/env python
import sys
import os
import glob
import wave
import soundfile as sf

def checkAudio(audioFile,format):
    # Verify if audio file is complete (check for truncate / missing bytes)
    if format == "wav":
        try:
            # Use Python's built-in Wave module
            # Result may be unreliable for WAVE files with bit depth of more than 16 bits, 
            # see below!!
            myWav = wave.open(audioFile, mode="rb")

            # Read parameters
            nchannels = myWav.getnchannels()
            sampwidth = myWav.getsampwidth()
            framerate = myWav.getframerate()
            nframes = myWav.getnframes()
                        
            # Read all audio frames     
            wavData = myWav.readframes(nframes)
            myWav.close()
            
            # Expected size of WavData in bytes
            sizeExpected = nframes*nchannels*(sampwidth)
            sizeActual = (len(wavData))
            
            if sizeActual < sizeExpected:
                isComplete = False
            else:
                isComplete = True
        except:
            # NOTE: some applications (e.g ffmpeg) add an 'extensible' flag to WAVE files
            # with a bit depth above 16 bits, which causes an exception in Python's Wave
            # module, in which case we also end up here!
            isComplete = False
            
    elif format == "flac":
        try:
            # Use Pysoundfile
            myFlac, samplerate = sf.read(audioFile)
            isComplete = True
        except:
            # If Flac is damaged it will cause an exception
            isComplete = False

    return(isComplete)
        

def main():

    #dataDir = os.path.normpath("E:\detectDamagedAudio\data")
    dataDir = os.path.normpath("E:/nimbieTest/test")
    filesWav = glob.glob(dataDir + "/*.wav")
    filesFlac = glob.glob(dataDir + "/*.flac")

    for fwav in filesWav:
        isCompleteFlag = checkAudio(fwav, "wav")
        print(fwav, isCompleteFlag)

    for fflac in filesFlac:
        isCompleteFlag = checkAudio(fflac, "flac")
        print(fflac, isCompleteFlag)

main()