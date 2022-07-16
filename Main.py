import os
import pandas as pd
from pydub import AudioSegment
from gtts import gTTS
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QTimer, QTime, QDate, Qt
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUiType
import sys
def TextToSpeechHindi(text, filename):
    mytext = str(text)
    language = 'hi'
    myobj = gTTS(text=mytext, lang=language, slow=False)
    myobj.save(filename)
def TextToSpeechEnglish(text, filename):
    mytext = str(text)
    language = 'en'
    myobj = gTTS(text=mytext, lang=language, slow=False)
    myobj.save(filename)
def TextToSpeechGujarati(text, filename):
    mytext = str(text)
    language = 'gu'
    myobj = gTTS(text=mytext, lang=language, slow=False)
    myobj.save(filename)
def mergeAudios(audios):
    combined = AudioSegment.empty()
    for audio in audios:
        combined += AudioSegment.from_mp3(audio)
    return combined
def GenerateSkeletonHindi():
    audio = AudioSegment.from_mp3('Clip.mp3')
    start = 87000
    finish = 88500
    audioProcessed = audio[start:finish]
    audioProcessed.export("H***.mp3", format="mp3")
    start = 110650
    finish = 112000
    audioProcessed = audio[start:finish]
    audioProcessed.export("H***.mp3", format="mp3")
    finish = 232000
    audioProcessed = audio[start:finish]
    audioProcessed.export("H***.mp3", format="mp3")
def GenerateSkeletonEnglish():
    audio = AudioSegment.from_mp3('Clip.mp3')
    start = 87000
    finish = 88500
    audioProcessed = audio[start:finish]
    audioProcessed.export("E***.mp3", format="mp3")
    start = 110650
    finish = 112000
    audioProcessed = audio[start:finish]
    audioProcessed.export("E***.mp3", format="mp3")
    start = 228000
    finish = 232000
    audioProcessed = audio[start:finish]
    audioProcessed.export("E***.mp3", format="mp3")
def GenerateSkeletonGujarati():
    audio = AudioSegment.from_mp3('Clip.mp3')
    start = 87000
    finish = 88500
    audioProcessed = audio[start:finish]
    audioProcessed.export("G***.mp3", format="mp3")
    start = 110650
    finish = 112000
    audioProcessed = audio[start:finish]
    audioProcessed.export("G***.mp3", format="mp3")
    start = 228000
    finish = 232000
    audioProcessed = audio[start:finish]
    audioProcessed.export("G***.mp3", format="mp3")
def GenerateAnnouncementHindi(filename):
    df = pd.read_excel(filename)
    print(df)
    for index, item in df.iterrows():
        TextToSpeechHindi(item['kri'], 'H***.mp3')
        TextToSpeechHindi(item['from'], 'H***.mp3')
        TextToSpeechHindi(item['se'], 'H***.mp3')
        TextToSpeechHindi(item['via'], 'H***.mp3')
        TextToSpeechHindi(item['ke'], 'H***.mp3')
        TextToSpeechHindi(item['to'], 'H***.mp3')
        TextToSpeechHindi(item['ko'], 'H***.mp3')
        TextToSpeechHindi(item['train_no'] + " " + item['train_name'], 'H***.mp3')
        TextToSpeechHindi(item['kuch'], 'H***.mp3')
        TextToSpeechHindi(item['platform'], 'H***.mp3')
        TextToSpeechHindi(item['par'], 'H***.mp3')
        audios = [f"{i}H***.mp3" for i in range(1,15)]
        announcement = mergeAudios(audios)
        announcement.export(f"AnnouncementH***_{index+1}.mp3", format="mp3")
def GenerateAnnouncementEnglish(filename):
    df = pd.read_excel(filename)
    print(df)
    for index, item in df.iterrows():
        TextToSpeechEnglish(item['Attention'], 'E***.mp3')
        TextToSpeechEnglish(item['train_no'] + "" + item['train_name'], 'E***.mp3')
        TextToSpeechEnglish(item['fr'], 'E***.mp3')
        TextToSpeechEnglish(item['from'], 'E***.mp3')
        TextToSpeechEnglish(item['t'], 'E***.mp3')
        TextToSpeechEnglish(item['to'], 'E***.mp3')
        TextToSpeechEnglish(item['v'], 'E***.mp3')
        TextToSpeechEnglish(item['via'], 'E***.mp3')
        TextToSpeechEnglish(item['is'], 'E***.mp3')
        TextToSpeechEnglish(item['platform'], 'E***.mp3')
        audios = [f"{i}E***.mp3" for i in range(1,14)]
        announcement = mergeAudios(audios)
        announcement.export(f"AnnouncementE***_{index+1}.mp3", format="mp3")
def GenerateAnnouncementGujarati(filename):
    df = pd.read_excel(filename)
    print(df)
    for index, item in df.iterrows():
        TextToSpeechGujarati(item['att'], 'G***.mp3')
        TextToSpeechGujarati(item['ga'], 'G***.mp3')
        TextToSpeechGujarati(item['train_no'], 'G***.mp3')
        TextToSpeechGujarati(item['train_name'], '5G***.mp3')
        TextToSpeechGujarati(item['from'], 'G***.mp3')
        TextToSpeechGujarati(item['se'], 'G***.mp3')
        TextToSpeechGujarati(item['via'], 'G***.mp3')
        TextToSpeechGujarati(item['viaa'], 'G***.mp3')
        TextToSpeechGujarati(item['to'], 'G***.mp3')
        TextToSpeechGujarati(item['mai'], 'G***.mp3')
        TextToSpeechGujarati(item['ich'], 'G***.mp3')
        TextToSpeechGujarati(item['sam'], 'G***.mp3')
        TextToSpeechGujarati(item['pla'], 'G***.mp3')
        TextToSpeechGujarati(item['nio'], 'G***.mp3')
        TextToSpeechGujarati(item['platform'], 'G***.mp3')
        TextToSpeechGujarati(item['par'], 'G***.mp3')
        TextToSpeechGujarati(item['ayu'], 'G***.mp3')
        TextToSpeechGujarati(item['rahi'], 'G***.mp3')
        TextToSpeechGujarati(item['che'], 'G***.mp3')
        audios = [f"{i}G***.mp3" for i in range(1,23)]
        announcement = mergeAudios(audios)
        announcement.export(f"AnnouncementG***_{index+1}.mp3", format="mp3")
def HindiOutPut():
    for i in range(1,3):
        sound1 = AudioSegment.from_mp3(f"AnnouncementH***_{i}.mp3")
        sound2 = AudioSegment.from_mp3(f"AnnouncementE***_{i}.mp3")
        combined = sound1 + sound2
        combined.export(f"FinalH***+English_OutPut_{i}.mp3", format='mp3')
def GujaratiOutPut():
    for i in range(1,3):
        sound1 = AudioSegment.from_mp3(f"AnnouncementG***_{i}.mp3")
        sound2 = AudioSegment.from_mp3(f"AnnouncementH***_{i}.mp3")
        sound3 = AudioSegment.from_mp3(f"AnnouncementE***_{i}.mp3")
        combined = sound1 + sound2 + sound3
        combined.export(f"FinalG***+Hindi+English_OutPut_{i}.mp3", format='mp3')
if __name__ == "__main__":
    print("Generating Skeleton...")
    GenerateSkeletonHindi()
    GenerateSkeletonEnglish()
    GenerateSkeletonGujarati()
    print("Now Generating Announcement...")
    GenerateAnnouncementHindi("DataH***.xlsx")
    GenerateAnnouncementEnglish("DataE***.xlsx")
    GenerateAnnouncementGujarati("DataG***.xlsx")
    HindiOutPut()
    GujaratiOutPut()