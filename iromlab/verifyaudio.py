#! /usr/bin/env python
import sys
import os
import glob
import wave
import soundfile as sf
import subprocess as sub
import time

def checkAudio(audioFile,format):
    # Verify if audio file is complete (check for truncated / missing bytes)
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

    # Define data directories
    dirWav = os.path.normpath("E:/nimbieTest/wav")
    dirFlac = os.path.normpath("E:/nimbieTest/flac")

    filesWav = glob.glob(dirWav + "/*.wav")
    filesFlac = glob.glob(dirFlac + "/*.flac")
    
    # Process WAVs
    startWav = time.time()

    for fwav in filesWav:
        isCompleteFlag = checkAudio(fwav, "wav")
        print(fwav, isCompleteFlag)
    
    endWav = time.time()
    elapsedWav = endWav - startWav
    print("Processing time WAVE: " + str(elapsedWav) + " seconds")
    
    # Process FLACs
    startFlac = time.time()
    
    for fflac in filesFlac:
        isCompleteFlag = checkAudio(fflac, "flac")
        print(fflac, isCompleteFlag)

    endFlac = time.time()
    elapsedFlac = endFlac - startFlac
    print("Processing time Flac: " + str(elapsedFlac) + " seconds")
    
    # Process WAVs with shntool
    shntool = os.path.normpath("C:/shntool/shntool.exe")
    
    startShn = time.time()
    for fwav in filesWav:
        args = [shntool, "info", fwav]
        p = sub.Popen(args,stdout=sub.PIPE,stderr=sub.PIPE)
        output, errors = p.communicate()
        print(output)
        print(errors)
    endShn = time.time()
    elapsedShn = endShn - startShn
    print("Processing time WAVE, shntool: " + str(elapsedShn) + " seconds")

    # Process FLACs with flac
    flactool = os.path.normpath("C:/flac/flac.exe")
    
    startFlac = time.time()
    for fflac in filesFlac:
        args = [flactool, "-t", fflac]
        p = sub.Popen(args,stdout=sub.PIPE,stderr=sub.PIPE)
        output, errors = p.communicate()
        print(output)
        print(errors)
    endFlac = time.time()
    elapsedFlac = endFlac - startFlac
    print("Processing time FLAC, flac: " + str(elapsedFlac) + " seconds")
    
    # Process FLACs with ffmpeg
    ffmpeg = "C:/ffmpeg/bin/ffmpeg.exe"
    
    startFlac = time.time()
    for fflac in filesFlac:
        # ffmpeg -v error -i foo.wav -f null -
        args = [ffmpeg, "-v", "error", "-i", fflac, "-f", "null", "-"]
        p = sub.Popen(args,stdout=sub.PIPE,stderr=sub.PIPE)
        output, errors = p.communicate()
        print(output)
        print(errors)
    endFlac = time.time()
    elapsedFlac = endFlac - startFlac
    print("Processing time FLAC, ffmpeg: " + str(elapsedFlac) + " seconds")
    
    
main()