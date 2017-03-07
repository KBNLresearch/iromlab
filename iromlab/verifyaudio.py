#! /usr/bin/env python
import glob
if __package__ == 'iromlab':
    from . import config
    from . import shared
else:
    import config
    import shared
    
def verifyAudioFile(audioFile, format):
    # Verify integrity of an audio file (check for missing / truncated bytes)
    
    if format == "wav":
        # Check with shntool
                
        args = [config.shntoolExe]
        #args = ["C:/Users/jkn010/iromlab/tools/shntool/shntool.exe"]
        args.append("info")
        args.append(audioFile)
    
        # Command line as string (used for logging purposes only)
        cmdStr = " ".join(args)
     
        status, out, err = shared.launchSubProcess(args)

        # Output lines to list
        outAsList = out.splitlines()
        noLines = len(outAsList)
       
        # Set up dictionary for storing values on reported problems
        problems = {}
        problemsAsList = []
        
        # Locate problems report
        startIndexProblems = shared.index_startswith_substring(outAsList, "Possible problems:")

        # Parse problems list and store as dictionary
        for i in range(startIndexProblems + 1, noLines, 1):
            thisLine = outAsList[i]
            lineAsList = thisLine.split(":")
            problemName = lineAsList[0].strip()
            problemValue = lineAsList[1].strip()
            problems[problemName] = problemValue
            problemsAsList.append(thisLine.strip())
        try:
            if problems["Inconsistent header"] != "no":
                isOK = False
            elif problems["File probably truncated"] != "no":
                isOK = False
            elif problems["Junk appended to file"] != "no":
                isOK = False
            else:
                isOK = True
        except KeyError:
                isOK = False

        # Add file reference as first element of errors list (used for logging only)
        problemsAsList.insert(0, "File: " + audioFile)
        return(isOK, status, problemsAsList)
        
    elif format == "flac":
        # Check with flac
        
        args = [config.flacExe]
        #args = ["C:/Users/jkn010/iromlab/tools/flac/win64/flac.exe"]
        args.append("-s")
        args.append("-t")
        args.append(audioFile)
    
        # Command line as string (used for logging purposes only)
        cmdStr = " ".join(args)
     
        status, out, err = shared.launchSubProcess(args)
       
        # Output lines to list (flac output is sent to stderr!)
        errAsList = err.splitlines()
        
        if(len(errAsList)) == 0:
            # No errors encountered
            isOK = True
        else:
            isOK = False
        
        # Add file reference as first element of errors list (used for logging only)
        errAsList.insert(0, "File: " + audioFile)
        return(isOK, status, errAsList)

def verifyCD(directory, format):
        # Verify audio with Shntool (wav) or flac (FLAC)
        
        # List of audio files to check
        filesAudio = glob.glob(directory + "/*." + format)
            
        # List to store error messages/ tool outputs for each file
        errorsList = []
    
        # Flag that signals the presence of audio (file) errors
        hasErrors = False
        
        # If filesAudio is empty list this indicates something is wrong
        # (note: this can happens if config.audioFormat does not match the
        # dBpoweramp's setting!)
        if filesAudio == []:
            hasErrors = True
        else:          
            for file in filesAudio:
                isOK, status, errors = verifyAudioFile(file, format)
                errorsList.append(errors)
                        
                if isOK == False or status != 0:
                    hasErrors = True
                            
        return(hasErrors, errorsList)
        
def main():

    import os
    import glob
    
    dirAudio = os.path.normpath("E:/detectDamagedAudio/data/")

    filesWav = glob.glob(dirAudio + "/*.wav")
    filesFlac = glob.glob(dirAudio + "/*.flac")

    """ 
    for fileWav in filesWav:
        isOK, status, errors = checkAudioFile(fileWav, "wav")
        print(fileWav, isOK, status)
        for error in errors:
            print(error)
    """
    
    for fileFlac in filesFlac:
        isOK, status, errors = verifyAudioFile(fileFlac, "wav")
        print(fileFlac, isOK, status)
        for error in errors:
            print(error)

if __name__ == "__main__":
    main()
