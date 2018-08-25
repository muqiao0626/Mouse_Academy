'''
Copyright (C) 2018 Meister Lab at Caltech 
-----------------------------------------------------
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import os, sys
import argparse
import traceback
import serial
import time
import re
import AcademyUtils

def getMegaSer(megaPort=None):
    if megaPort is None:
        megaPort = AcademyUtils.findMegaPort()
    megaSer = serial.Serial(megaPort, 9600, timeout=1)
    try:
        setupMsg = megaSer.readline().decode().strip()
    except Exception as e:
        raise ReadError('No setup message:\n%s' %e)
    time.sleep(0.05)
    try:
        readyMsg = megaSer.readline().decode().strip()
    except Exception as e:
        raise ReadError('No ready message:\n%s' %e)
    
    return megaSer

def resetMega(megaSer):
    megaSer.close()
    newSer = getMegaSer()
    return newSer

#write two-byte code for reading tag from RFID reader serial input
def readTag(megaSer, readerNum):
    megaSer.reset_output_buffer()
    megaSer.reset_input_buffer()
    commandStr = '8%d' % readerNum
    megaSer.write(commandStr.encode())
    completeMsg = False
    for check in range(3):
        time.sleep(0.05)
        msgstr = megaSer.readline()
        try:
            msgstr = msgstr.decode().strip()
        except UnicodeDecodeError:
            print('UnicodeDecodeError:', msgstr)
            msgstr = ''
        completeMsg = "read tag complete" in msgstr.lower()
        if completeMsg:
            #rString = megaSer.readline()
            break
    if not completeMsg:
        raise ReadError('Did not receive message indicating completed read.')
    charList = ['!' for x in range(12)]
    for b in range(1, 13):
        try:
            readByte = megaSer.read()
            charList[b-1] = readByte.decode()
        except UnicodeDecodeError:
            #clear input buffer
            print('UnicodeDecodeError')
            print(charList, readByte)
            megaSer.reset_input_buffer()
            break
    tagString = ''.join(charList)
    megaSer.read(2)
    #if isinstance(rString, bytes):
    #    try:
    #        print(rString)
    #        rString = rString.decode()
    #    except UnicodeDecodeError as ude:
    #        raise ReadError("Failed at: %s" % rString)
    #rString = rString.strip()
    return searchForTag(tagString)

#read all tags available in reader's serial buffer
def clearBuffer(megaSer, readerNum):
    buffer = np.array([])
    tagInBuffer = True
    timeout = 0.2
    startTime = time.time()
    while tagInBuffer:
        try:
            newTag = readTag(megaSer, readerNum)
        except ReadError:
            megaSer.reset_input_buffer()
            megaSer.reset_output_buffer()
            newTag = "000000000000"
        elapsed = time.time()-startTime
        if elapsed > timeout:
            return buffer
        else:
            tagInBuffer = isTag(newTag)
            if tagInBuffer:
                buffer = np.append(buffer, newTag)
            
    return buffer

#write two-byte code for operating servo to open door
def openDoor(megaSer, servoNum):
    commandStr = '6%d' % servoNum
    megaSer.write(commandStr.encode())
    completeMsg = False
    time.sleep(1)
    msgstr = megaSer.readline().decode()
    completeMsg = "open door complete" in msgstr.lower()
    if not completeMsg:
        reset()
        #raise ServoError('Door %d failed to open: %s' % (servoNum, msgstr))
    
#write two-byte coe for operating servo to close door
def closeDoor(megaSer, servoNum):
    commandStr = '7%d' % servoNum
    megaSer.write(commandStr.encode())
    completeMsg = False
    time.sleep(1)
    msgstr = megaSer.readline().decode()
    completeMsg = "close door complete" in msgstr.lower()
    obstructionMsg = "bstruction" in msgstr.lower()
    if not completeMsg:
        if obstructionMsg:
            print(obstructionMsg)
            raise ServoError('Door %d reopened due to obstruction.' % servoNum)
        else:
            reset()
            #raise ServoError('Door %d failed to close.' % servoNum)

    
def resetMega():
    global arduinoPort
    global megaSer
    global door1open
    global door2open
    megaSer.close()
    megaSer = serial.Serial(arduinoPort, 9600)
    megaSer.readline()
    if door1open:
        openDoor(megaSer, 1)
    else:
        closeDoor(megaSer, 1)
    if door2open:
        openDoor(megaSer, 2)
    else:
        closeDoor(megaSer, 2)
    return megaSer
    
def searchForTag(searchString):
    try:
        matchObj = re.search('[0-9A-Fa-f]{12}', searchString)
    except (TypeError, AttributeError) as err:
        idIn = ''
    try:
        idIn = matchObj.group(0)
    except (TypeError, AttributeError) as typerr:
        idIn = ''
    return idIn
   
def isTag(tagString, taglen=12):
    if isinstance(tagString, str) and len(tagString)==taglen and tagString!= "000000000000":
        matchObj = re.search('[0-9A-Fa-f]{12}', tagString)
        if matchObj is None: #string isn't completely hex characters
            return False
        else:
            return True
    else:
        return False
class ServoError(Exception):
    def __init__(self, message):
        self.message = message

class ReadError(Exception):
    def __init__(self, message):
        self.message = message
