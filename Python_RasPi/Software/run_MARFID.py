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
import numpy as np
import time
import json
import re
import serial
from serial.tools.list_ports_linux import comports
import importlib
import BpodClass
import AcademyUtils
import OpenMV.recordMjpeg as recorder
from ReportCardClass import ReportCard
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
    global megaPort
    global door1open
    global door2open
    global read1
    global read2
    global read3
    global tag1
    global tag2
    global tag3
    
    #only allow numbers in input
    numSubjectsInp = input('How many subjects? (up to 5) ')
    while not numSubjectsInp.isdigit():
        numSubjectsInp = input('Please enter an integer value.\nHow many subjects? ')
    #only allow number <= 5
    numSubjects = int(numSubjectsInp)
    if numSubjects > 5:
        print('Number of subjects must be no greater than 5.')
        numSubjects = 5
    
    reportCards = {}
    for sub in range(1, numSubjects+1):
        subject = input('Name of subject %d? ' %sub)
        rc = ReportCard(subject)
        yn = input('Current protocol for "%s" is "%s". Change protocol? (y/n)' %(subject, rc.currentProtocol))
        if yn.lower()=='y' or yn.lower()=='n':
            ynGood = True
        else:
            ynGood = False
        while not ynGood:
            yn = input('Current protocol for "%s" is "%s". Change protocol? (y/n)' %(subject, rc.currentProtocol))
            if yn.lower()=='y' or yn.lower()=='n':
                ynGood = True
        if yn=='y':
            protInp = input('Enter new protocol for "%s": ' %subject)
            print('Setting protocol for %s to %s.' %(subject, protInp))
            rc.setCurrentProtocol(protInp)
        reportCards.update({subject:rc})
        
    megaSer = MegaCom.getMegaSer()
    bpodPort = AcademyUtils.findBpodUSBPort()
    AcademyUtils.resetBpodPort()
    
    tagIDtoSubject = AcademyUtils.getRoster()
    
        
    startTime = time.time()
    elapsed_time = 0

    camSer, connected = OpenMVCom.connect()
    if connected:
        print("Successful connection to OpenMV cam.")
    else:
        print("Could not connect to OpenMV cam.")
    idIn = ""

    door1open = True
    door2open = False
    MegaCom.openDoor(megaSer, 1)
    MegaCom.closeDoor(megaSer, 2)
    while elapsed_time < 6*3600:
    #try all readers for tag
        tracking = 'M0'
        tag1 = MegaCom.readTag(megaSer, 1)
        tag2 = MegaCom.readTag(megaSer, 2)
        read1 = MegaCom.isTag(tag1)
        read2 = MegaCom.isTag(tag2)
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
                MegaCom.closeDoor(megaSer, 1)
            except ServoError as e:
                print("Door unable to close. Resetting reader buffers.")
                buff1 = MegaCom.clearBuffer(megaSer, 1)
                buff2 = MegaCom.clearBuffer(megaSer, 2)
                continue
            door2open = True
            MegaCom.openDoor(megaSer, 2)
            passedTrainingDoor = False
            while not passedTrainingDoor:
                tag3 = MegaCom.readTag(megaSer, 3)
                time.sleep(0.1)
                read3 = MegaCom.isTag(tag3)
                if read3:
                    print("mouse %s began training" % tracking)
                    door2open = False
                    try:
                        MegaCom.closeDoor(megaSer, 2)
                        passedTrainingDoor = True
                    except ServoError as e:
                        print("Unable to close door 2.")
                        passedTrainingDoor = False
                        continue
                    try:
                        compTimeObj = OpenMVCom.startRecording(camSer)
                    except serial.serialutil.SerialException:
                        print('SerialException: OpenMV cam not connected.')
                    protocol = importlib.import_module(reportCards[tracking].currentProtocol,
                                                                                     package=reportCards[tracking].currentProtocol)
                    print(protocol)
                    try:
                        myBpod, reportCards[tracking] = protocol.runProtocol(bpodPort, reportCards[tracking])
                    except:
                        print("Bpod exception.")
                        AcademyUtils.resetBpodPort()
                    try:
                        actualStartTimeObj, endTimeObj, dur = OpenMVCom.stopRecording(camSer)
                    except OpenMVError as e:
                        print('Camera failure:\n%s' %e)
                    #clear buffer 2 so we can read when
                    #training mouse passes reader 2
                    buff2 = MegaCom.clearBuffer(megaSer, 2)
                    print("Emptied buffer from reader 2:")
                    print(buff2)
                    door2open = True
                    MegaCom.openDoor(megaSer, 2)
                    exitedTraining = False
                    while not exitedTraining:
                        tag2 = MegaCom.readTag(megaSer, 2)
                        time.sleep(0.1)
                        read2 = MegaCom.isTag(tag2)
                        if read2 and tracking==tagIDtoSubject["id"][tag2]["mouseID"]:
                            exitedTraining = True
                            door2open = False
                            try:
                                MegaCom.closeDoor(megaSer, 2)
                                print("mouse %s exited training" % tracking)
                            except ServoError as e:
                                print("Unable to close door 2.")
                                exitedTraining = False
                                continue
                            print("Emptied buffer from reader 3:")
                            buff3 = MegaCom.clearBuffer(megaSer, 3)
                            print(buff3)
                            print("Emptied buffer from reader 1:")
                            buff1 = MegaCom.clearBuffer(megaSer, 1)
                            print(buff1)
                            door1open = True
                            try:
                                MegaCom.openDoor(megaSer, 1)
                            except ServoError:
                                reset()
                            returnedHome = False
                            while not returnedHome:
                                time.sleep(0.1)
                                tag1 = MegaCom.readTag(megaSer, 1)
                                if isTag(tag1) and tracking==tagIDtoSubject["id"][tag1]["mouseID"]:
                                    returnedHome = True
                                    buff2 = MegaCom.clearBuffer(megaSer, 2)
                                    print("mouse %s returned to home cage" % tracking)
        elapsed_time = time.time()-startTime
    
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
    MegaCom.resetMega(megaSer)
    if door1open:
        MegaCom.openDoor(megaSer, 1)
    else:
        MegaCom.closeDoor(megaSer, 1)
    if door2open:
        MegaCom.openDoor(megaSer, 2)
    else:
        MegaCom.closeDoor(megaSer, 2)
    return reset

if __name__ == '__main__':
    main()
