#! /usr/bin/env python
if __package__ == 'iromlab':
    from . import config
    from . import shared
else:
    import config
    import shared
    
def checkAudio(audioFile, format):
    # Verify integrity of an audio file (check for missing / truncated bytes)
    
    if format == "wave":
        # Check with shntool
        
        #args = [config.shntoolExe]
        args = ["C:/Users/jkn010/iromlab/tools/shntool/shntool.exe"]
        args.append( "info")
        args.append(audioFile)
    
        # Command line as string (used for logging purposes only)
        cmdStr = " ".join(args)
     
        status, out, err = shared.launchSubProcess(args)

        # Output lines to list
        outAsList = out.splitlines()
        noLines = len(outAsList)
       
        # Set up dictionary for storing values on reported problems
        problems = {}
        
        # Locate problems report
        startIndexProblems = shared.index_startswith_substring(outAsList, "Possible problems:")

        # Parse problems list and store as dictionary
        for i in range(startIndexProblems + 1, noLines, 1):
            thisLine = outAsList[i]
            thisLine = thisLine.split(":")
            problemName = thisLine[0].strip()
            problemValue = thisLine[1].strip()
            problems[problemName] = problemValue
        try:
            if problems["File probably truncated"] != "no":
                isComplete = False
            else:
                isComplete = True
        except KeyError:
                isComplete = False
                
        return(isComplete, status)
    
def main():
    audioFile = "E:/nimbieTest/wav/01.wav"
    checkAudio(audioFile, "wave")

main()
