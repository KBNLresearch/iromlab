#! /usr/bin/env python
import sys
import os
from pydub import AudioSegment

audioFile = os.path.normpath("E:/detectDamagedAudio/data/frogs-01-last-byte-missing.wav")

song = AudioSegment.from_file(audioFile, "wave")

rawData = song.raw_data

print(song.channels)
print(song.frame_rate)
print(song.sample_width*8) # sample width = bit depth in bytes!

