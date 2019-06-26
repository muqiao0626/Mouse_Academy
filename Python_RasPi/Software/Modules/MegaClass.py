'''
6/22/19
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
from datetime import datetime
import re
import AcademyUtils
import numpy as np

class MegaObject(object):
    def __init__(self, megaPName=None, unoPName=None):
        self.megaPortName = megaPName
        self.unoPortName = unoPName
        self.megaSer = None
        self.unoSer = None
        self.door1open = None
        self.door2open = None
        self.tag1read = False
        self.tag2read = False
        self.tag3read = False
        self.tag1 = "000000000000"
        self.tag2 = "000000000000"
        self.tag3 = "000000000000"
        self.lightsOn = None
        self.lightsOff = None
        self.isLogging = False
        if self.megaPortName == None:
            self.megaPortName = AcademyUtils.findMegaPort()
        self.megaSer = self.getMegaSer()
        
        if self.unoPortName == None:
            self.unoPortName = AcademyUtils.findUnoPort()
        self.unoSer = self.getUnoSer()


    def getMegaSer(self, megaPort=None):
        if megaPort is None:
            megaPort = self.megaPortName
        self.megaSer = serial.Serial(megaPort, 9600, timeout=1)
        try:
            setupMsg = self.megaSer.readline().decode().strip()
        except Exception as e:
            raise ReadError('No setup message:\n%s' %e)
        time.sleep(0.05)
        try:
            readyMsg = self.megaSer.readline().decode().strip()
        except Exception as e:
            self.megaSer = None
    
        return self.megaSer

    def getUnoSer(self, unoPort=None):
        if unoPort is None:
            unoPort = self.unoPortName
        self.unoSer = serial.Serial(unoPort, 9600, timeout=1)
        try:
            initMsg = unoSer.readline().decode().strip()
        except Exception as e:
            try:
                self.unoSer = serial.Serial(self.unoPortName, 9600, timeout=1)
            except:
                self.unoPortName = AcademyUtils.findUnoPort()
                self.unoSer = serial.Serial(self.unoPortName, 9600, timeout=1)
        time.sleep(0.05)
    
        return self.unoSer

    def resetMega(self, megaSer=None):
        if megaSer == None:
            megaSer = self.megaSer
        megaSer.close()
        newSer = self.getMegaSer()
        return newSer

    #write two-byte code for reading tag from RFID reader serial input
    def beginLogging(self, unoSer=None):
        if unoSer==None:
            unoSer = self.unoSer
        startTime = time.time()
        startTimeObj = datetime.fromtimestamp(startTime)
        compTime = int(1000*startTime)
        unoSer.write('51'.encode())
        unoSer.write(str(compTime).encode())
    
        beginMsg = False
        for check in range(3):
            time.sleep(0.05)
            msgstr = unoSer.readline()
            #print(msgstr)
            try:
                msgstr = msgstr.decode().strip()
            except UnicodeDecodeError:
                print('UnicodeDecodeError:', msgstr)
                msgstr = ''
            beginMsg = "begin logging" in msgstr.lower()
            if beginMsg:
                self.isLogging = True
                break
        if not beginMsg:
            self.isLogging = False
            raise ReadError('Did not receive message indicating logging begun:\n%s' %msgstr)
    
    #write two-byte code for reading tag from RFID reader serial input
    def endLogging(self, unoSer=None):
        if unoSer==None:
            unoSer = self.unoSer
        commandStr = '50'
        unoSer.write(commandStr.encode())
    
        endMsg = False
        for check in range(3):
            time.sleep(0.05)
            msgstr = unoSer.readline()
            #print(msgstr)
            try:
                msgstr = msgstr.decode().strip()
            except UnicodeDecodeError:
                print('UnicodeDecodeError:', msgstr)
                msgstr = ''
            endMsg = "end logging" in msgstr.lower()
            if endMsg:
                self.isLogging = False
                break
        if not endMsg:
            self.isLogging = False
            raise ReadError('Did not receive message indicating logging ended:\n%s' %msgstr)
    
    #write two-byte code for reading tag from RFID reader serial input
    def readTag(self, readerNum):
        self.megaSer.reset_output_buffer()
        self.megaSer.reset_input_buffer()
        commandStr = '8%d' % readerNum
        self.megaSer.write(commandStr.encode())
        completeMsg = False
        for check in range(3):
            time.sleep(0.05)
            msgstr = self.megaSer.readline()
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
        tagString = self.megaSer.readline().decode().strip()
        #print(tagString)
    
        if readerNum == 1:
            tag1 = self.searchForTag(tagString)
            self.tag1 = tag1
            return tag1
        elif readerNum == 2:
            tag2 = self.searchForTag(tagString)
            self.tag2 = tag2
            return tag2
        elif readerNum == 3:
            tag3 = self.searchForTag(tagString)
            self.tag3 = tag3
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
    def clearBuffer(self, readerNum):
        buffer = np.array([])
        tagInBuffer = True
        timeout = 0.2
        startTime = time.time()
        while tagInBuffer:
            try:
                newTag = self.readTag(readerNum)
            except ReadError:
                self.megaSer.reset_input_buffer()
                self.megaSer.reset_output_buffer()
                newTag = "000000000000"
            elapsed = time.time()-startTime
            if elapsed > timeout:
                return buffer
            else:
                tagInBuffer = self.isTag(newTag)
                if tagInBuffer:
                    buffer = np.append(buffer, newTag)
            
        return buffer

    #write two-byte code for operating servo to open door
    def openDoor(self, servoNum):
        commandStr = '6%d' % servoNum
        self.megaSer.write(commandStr.encode())
        completeMsg = False
        time.sleep(1)
        msgstr = self.megaSer.readline().decode()
        completeMsg = "open door complete" in msgstr.lower()
        if not completeMsg:
            raise MegaComError('Mega not responding; door %d failed to open: %s' % (servoNum, msgstr))
        else:
            if servoNum == 1:
                self.door1open = True
            elif servoNum == 2:
                self.door2open = True
            else:
                raise MegaComError('Error: servoNum must be 1 or 2.')
        
    #write two-byte code for checking if mouse at reader 1
    def tag1InRange(self):
        commandStr = '90' 
        self.megaSer.write(commandStr.encode())
        time.sleep(0.005)
        msgstr = self.megaSer.readline().decode()
        try:
            tir1 = "true" in msgstr.lower()
        except:
            raise MegaComError('tag1InRange failed, message: %s' % msgstr)
        
        return tir1
    
    #write two-byte code for turning lights on
    def turnLightsOn(self):
        commandStr = '51' 
        self.megaSer.write(commandStr.encode())
        time.sleep(0.005)
        msgstr = self.megaSer.readline().decode()
        try:
            self.lightsOn = "on" in msgstr.lower()
            self.lightsOff = not self.lightsOn
            return self.lightsOn
        except:
            raise MegaComError('Lights ON failed, message: %s' % msgstr)
    
    #write two-byte code for turning lights off
    def turnLightsOff(self):
        commandStr = '52' 
        self.megaSer.write(commandStr.encode())
        time.sleep(0.005)
        msgstr = self.megaSer.readline().decode()
        try:
            self.lightsOff = "off" in msgstr.lower()
            self.lightsOn = not self.lightsOff
            return self.lightsOff
        except:
            raise MegaComError('Lights OFF failed, message: %s' % msgstr)
    
    #write two-byte coe for operating servo to close door
    def closeDoor(self, servoNum):
        commandStr = '7%d' % servoNum
        self.megaSer.write(commandStr.encode())
        completeMsg = False
        time.sleep(1)
        msgstr = self.megaSer.readline().decode()
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
                self.door1open = False
            elif servoNum == 2:
                self.door2open = False
            else:
                raise MegaComError('Error: servoNum must be 1 or 2.')

    
    def resetMega(self):
        print('Resetting Arduino Mega...')
        self.megaSer.close()
        self.megaSer = self.getMegaSer()
        if door1open:
            self.openDoor(1)
        else:
            self.closeDoor(1)
        if door2open:
            self.openDoor(2)
        else:
            self.closeDoor(2)
        if self.lightsOn:
            self.turnLightsOn()
        else:
            self.turnLightsOff()
        return self.megaSer
    
    def resetUno(self):
        print('Resetting Arduino Uno...')
        self.unoSer.close()
        self.unoSer = self.getUnoSer()
        self.isLogging = False
        return self
    
    def searchForTag(self, searchString):
        try:
            matchObj = re.search('[0-9A-Fa-f]{12}', searchString)
        except (TypeError, AttributeError) as err:
            idIn = ''
        try:
            idIn = matchObj.group(0)
        except (TypeError, AttributeError) as typerr:
            idIn = ''
        return idIn
   
    def isTag(self, tagString, taglen=12):
        if isinstance(tagString, str) and len(tagString)==taglen and tagString!= "000000000000":
            matchObj = re.search('[0-9A-Fa-f]{12}', tagString)
            if matchObj is None: #string isn't completely hex characters
                return False
            else:
                return True
        else:
            return False
    def disconnect(self):
        self.megaSer.close()
        self.unoSer.close()
class ServoError(Exception):
    pass

class ReadError(Exception):
    pass

class MegaComError(Exception):
    pass