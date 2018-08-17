import os, sys
import argparse
import numpy as np
import time
import json
import re
import serial
from serial.tools.list_ports_linux import comports
import importlib
import BpodClass
import BpodUtils
import OpenMV.recordMjpeg as recorder
import report_card as rc
door1open = True
door2open = False
megaSer = None
tag1 = "000000000000"
tag2 = "000000000000"
tag3 = "000000000000"
read1 = False
read2 = False
read3 = False

def main():
    global megaSer
    global arduinoPort
    global door1open
    global door2open
    global read1
    global read2
    global read3
    global tag1
    global tag2
    global tag3
    m5 = rc.ReportCard('M5')
    m6 = rc.ReportCard('M6')
    m7 = rc.ReportCard('M7')
    #test tags
    m00 = rc.ReportCard('M00')
    m01 = rc.ReportCard('M01')
    m02 = rc.ReportCard('M02')
    m8 = rc.ReportCard('M8')
    m9 = rc.ReportCard('M9')
    m10 = rc.ReportCard('M10')
    m11 = rc.ReportCard('M11')
    reportCards = {'M00':m00, 'M01':m01, 'M02':m02, 'M6': m6, 'M7': m7, 'M8':m8, 'M9': m9, 'M10': m10, 'M11': m11}
    devices = BpodUtils.getDevices()
    arduinoPort, megaSer = BpodUtils.findMegaPort()
    camPort = devices['OpenMV Virtual Comm Port in FS Mode']
    bpodPort = BpodUtils.findBpodUSBPort()
    bpodResetPort = BpodUtils.findBpodProgPort()
    serial.Serial(bpodResetPort, 9600, timeout=0).close()
    
    tagIDtoSubject = BpodUtils.getTagToSub()
    
        
    startTime = time.time()
    elapsed_time = 0

    camSer = serial.Serial(camPort, 9600, timeout=1)
    time.sleep(2)
    connected = camSer.read().decode()
    print('connected: ', connected)
    if connected:
        print("Successful connection to OpenMV cam.")
    else:
        print("Could not connect to OpenMV cam.")
    idIn = ""

    door1open = True
    door2open = False
    openDoor(megaSer, 1)
    closeDoor(megaSer, 2)
    while elapsed_time < 6*3600:
    #try all readers for tag
        tracking = 'M0'
        tag1 = readTag(megaSer, 1)
        tag2 = readTag(megaSer, 2)
        read1 = isTag(tag1)
        read2 = isTag(tag2)
        #print('tag2: ', tag2)
        #print('read2: ', read2)
        if not read2:
            elapsed_time = time.time()-startTime  
        else: #wait for mouse to pass
            #find which mouse we're keeping track of
            tracking = tagIDtoSubject["id"][tag2]["mouseID"]
            if not reportCards[tracking].trainingAllowed:
                print("Mouse %s not permitted to train." % tracking)
                continue
            print("mouse %s passed checkpoint" % tracking)
            door1open = False
            try:
                closeDoor(megaSer, 1)
            except ServoError as e:
                print("Door unable to close. Resetting reader buffers.")
                buff1 = clearBuffer(megaSer, 1)
                buff2 = clearBuffer(megaSer, 2)
                continue
            door2open = True
            openDoor(megaSer, 2)
            passedTrainingDoor = False
            while not passedTrainingDoor:
                tag3 = readTag(megaSer, 3)
                time.sleep(0.1)
                read3 = isTag(tag3)
                if read3:
                    print("mouse %s began training" % tracking)
                    door2open = False
                    try:
                        closeDoor(megaSer, 2)
                        passedTrainingDoor = True
                    except ServoError as e:
                        print("Unable to close door 2.")
                        passedTrainingDoor = False
                        continue
                    try:
                        compTime = recorder.startRecording(camSer)
                    except serial.serialutil.SerialException:
                        print('SerialException: OpenMV cam not connected.')
                    protocol = importlib.import_module('Bpod_Gen2.Python_3.%s.%s' % (reportCards[tracking].currentProtocol,
                                                                                     reportCards[tracking].currentProtocol), package=None)
                    print(protocol)
                    megaSer.close()
                    try:
                        myBpod, reportCards[tracking] = protocol.runProtocol(bpodPort, reportCards[tracking])
                    except:
                        print("Bpod exception.")
                        serial.Serial(bpodResetPort, 9600, timeout=0).close()
                    megaSer.open()
                    megaSer.readline()
                    megaSer.readline()
                    try:
                        ct, actualDuration = recorder.stopRecording(camSer, compTime)
                    except:
                        print('Camera failure.')
                    #clear buffer 2 so we can read when
                    #training mouse passes reader 2
                    buff2 = clearBuffer(megaSer, 2)
                    print("Emptied buffer from reader 2:")
                    print(buff2)
                    door2open = True
                    openDoor(megaSer, 2)
                    exitedTraining = False
                    while not exitedTraining:
                        tag2 = readTag(megaSer, 2)
                        time.sleep(0.1)
                        read2 = isTag(tag2)
                        if read2 and tracking==tagIDtoSubject["id"][tag2]["mouseID"]:
                            exitedTraining = True
                            door2open = False
                            try:
                                closeDoor(megaSer, 2)
                                print("mouse %s exited training" % tracking)
                            except ServoError as e:
                                print("Unable to close door 2.")
                                exitedTraining = False
                                continue
                            print("Emptied buffer from reader 3:")
                            buff3 = clearBuffer(megaSer, 3)
                            print(buff3)
                            print("Emptied buffer from reader 1:")
                            buff1 = clearBuffer(megaSer, 1)
                            print(buff1)
                            door1open = True
                            try:
                                openDoor(megaSer, 1)
                            except ServoError:
                                reset()
                            returnedHome = False
                            while not returnedHome:
                                time.sleep(0.1)
                                tag1 = readTag(megaSer, 1)
                                if isTag(tag1) and tracking==tagIDtoSubject["id"][tag1]["mouseID"]:
                                    returnedHome = True
                                    buff2 = clearBuffer(megaSer, 2)
                                    print("mouse %s returned to home cage" % tracking)
        elapsed_time = time.time()-startTime
            
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
    

#what to do if arduino resets
def reset():
    reset = True
    global megaSer
    global door1open
    global door2open
    global read1
    global read2
    global read3
    global tag1
    global tag2
    global tag3
    print("door1open: ", door1open)
    print("door2open: ", door2open)
    resetSer(megaSer)
    settingUpMsg = megaSer.readline()
    time.sleep(0.05)
    readyMessage = megaSer.readline()
    if door1open:
        openDoor(megaSer, 1)
    else:
        closeDoor(megaSer, 1)
    if door2open:
        openDoor(megaSer, 2)
    else:
        closeDoor(megaSer, 2)
    return reset

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

if __name__ == '__main__':
    main()
