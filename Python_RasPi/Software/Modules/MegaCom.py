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
import numpy as np

#Initialize global variables
def init():
    
    global megaSer
    global megaPort
    global door1open
    global door2open
    global read1
    global read2
    global read3
    global tag1
    global tag2
    global tag3
    
    door1open = True
    door2open = False
    megaSer = None
    tag1 = "000000000000"
    tag2 = "000000000000"
    tag3 = "000000000000"
    read1 = False
    read2 = False
    read3 = False
    megaPort = AcademyUtils.findMegaPort()
    megaSer = getMegaSer(megaPort)
    
    globalVars = {'door1open':door1open,
                  'door2open':door2open,
                  'megaSer':megaSer,
                  'tag1':tag1,
                  'tag2':tag2,
                  'tag3':tag3,
                  'read1':read1,
                  'read2':read2,
                  'read3':read3,
                  'megaSer':megaSer
        }
    return globalVars

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
        #print(msgstr)
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
        raise ReadError('Did not receive message indicating completed read:\n%s' %msgstr)
    time.sleep(0.01)
    tagString = megaSer.readline().decode().strip()
    #print(tagString)
    
    if readerNum == 1:
        tag1 = searchForTag(tagString)
        return tag1
    elif readerNum == 2:
        tag2 = searchForTag(tagString)
        return tag2
    elif readerNum == 3:
        tag3 = searchForTag(tagString)
        return tag3
    else:
        raise MegaComError('Error: readerNum must be 1, 2, or 3.')
    #if isinstance(rString, bytes):
    #    try:
    #        print(rString)
    #        rString = rString.decode()
    #    except UnicodeDecodeError as ude:
    #        raise ReadError("Failed at: %s" % rString)

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
    global door1open
    global door2open
    commandStr = '6%d' % servoNum
    megaSer.write(commandStr.encode())
    completeMsg = False
    time.sleep(1)
    msgstr = megaSer.readline().decode()
    completeMsg = "open door complete" in msgstr.lower()
    if not completeMsg:
        raise MegaComError('Mega not responding; door %d failed to open: %s' % (servoNum, msgstr))
    else:
        if servoNum == 1:
            door1open = True
        elif servoNum == 2:
            door2open = True
        else:
            raise MegaComError('Error: servoNum must be 1 or 2.')
        
#write two-byte code for checking if mouse at reader 1
def tag1InRange(megaSer):
    commandStr = '90' 
    megaSer.write(commandStr.encode())
    time.sleep(0.005)
    msgstr = megaSer.readline().decode()
    try:
        tir1 = "false" not in msgstr.lower()
    except:
        raise MegaComError('tag1InRange failed, message: %s' % msgstr)
    
#write two-byte coe for operating servo to close door
def closeDoor(megaSer, servoNum):
    global door1open
    global door2open
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
            raise MegaComError('Mega not responding; door %d failed to close:\n%s' % (servoNum, msgstr))
    else:
        if servoNum == 1:
            door1open = False
        elif servoNum == 2:
            door2open = False
        else:
            raise MegaComError('Error: servoNum must be 1 or 2.')

    
def resetMega():
    global megaPort
    global megaSer
    global door1open
    global door2open
    megaSer.close()
    megaSer = serial.Serial(megaPort, 9600)
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
    pass

class ReadError(Exception):
    pass

class MegaComError(Exception):
    pass
