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
import OpenMVCom
from ReportCardClass import ReportCard
import MegaCom


def main():
    
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
    subToTag = AcademyUtils.getSubjectToTag()
    for sub in range(1, numSubjects+1):
        subject = input('Name of subject %d? ' %sub)
        while subject not in subToTag:
            subject = input('"%s" not enrolled.\nName of subject %d? ' %(subject, sub))
            
        rc = ReportCard(subject)
        rc.tagID = subToTag[subject]
        print(subject + ':', rc.tagID)
        
        if rc.getWaterToday()<rc.maxWater:
            rc.trainingAllowed = True
        rc.save()
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
        
    globalVars = MegaCom.init()
    bpodPort = AcademyUtils.findBpodUSBPort()
    AcademyUtils.resetBpodPort()
    
    tagIDtoSubject = AcademyUtils.getRoster()
    
        
    startTime = time.time()
    elapsed_time = 0
    
    try:
        camSer, connected = OpenMVCom.connect()
    except AcademyUtils.DeviceError as e:
        print(e)
        connected = False
        
    if connected:
        print("Successful connection to OpenMV cam.")
    else:
        print("Could not connect to OpenMV cam.")
    idIn = ""

    MegaCom.openDoor(globalVars['megaSer'], 1)
    try:
        MegaCom.closeDoor(globalVars['megaSer'], 2)
    except:
        print('door 2 failed to close')
    MegaCom.closeDoor(globalVars['megaSer'], 2)
    while elapsed_time < 9*3600:
    #try readers 1 and 2 for tag
        tracking = None
        globalVars['tag1'] = MegaCom.readTag(globalVars['megaSer'], 1)
        time.sleep(0.1) #attempting to read tags too quickly causes
                        #errors in communicating with mega
        globalVars['tag2'] = MegaCom.readTag(globalVars['megaSer'], 2)
        time.sleep(0.1)
        globalVars['read1'] = MegaCom.isTag(globalVars['tag1'])
        globalVars['read2'] = MegaCom.isTag(globalVars['tag2'])
        #print('tag2: ', tag2)
        #print('read2: ', read2)
        if not globalVars['read2']:
            elapsed_time = time.time()-startTime  
        else: #wait for mouse to pass
            #find which mouse we're keeping track of
            tracking = tagIDtoSubject["id"][globalVars['tag2']]["mouseID"]
            #if animal is not allowed to train, wait for
            #animal to return to home cage, then clear buffers
            if not reportCards[tracking].trainingAllowed:
                print("Mouse %s not permitted to train." % tracking)
                returnedHome = False
                while not returnedHome:
                    globalVars['tag1'] = MegaCom.readTag(globalVars['megaSer'], 1)
                    time.sleep(0.05)
                    globalVars['read1'] = MegaCom.isTag(globalVars['tag1'])
                    if globalVars['read1']:
                        if globalVars['tag1']==reportCards[tracking].tagID:
                            returnedHome = True
                            print('Mouse %s returned to home cage' % tracking)
                            buff1 = MegaCom.clearBuffer(globalVars['megaSer'], 1)
                            buff2 = MegaCom.clearBuffer(globalVars['megaSer'], 2)
            #if animal is allowed to train:
            else:            
                if not MegaCom.tag1InRange(globalVars['megaSer']):
                    print("Mouse %s passed checkpoint." % tracking)
                    try:
                        MegaCom.closeDoor(globalVars['megaSer'], 1)
                    except MegaCom.ServoError as e:
                        print("Door unable to close. Resetting reader buffers.")
                        buff1 = MegaCom.clearBuffer(globalVars['megaSer'], 1)
                        buff2 = MegaCom.clearBuffer(globalVars['megaSer'], 2)
                        continue
                    MegaCom.openDoor(globalVars['megaSer'], 2)
                    passedTrainingDoor = False
                    while not passedTrainingDoor:
                        globalVars['tag3'] = MegaCom.readTag(globalVars['megaSer'], 3)
                        time.sleep(0.1)
                        globalVars['read3'] = MegaCom.isTag(globalVars['tag3'])
                        if globalVars['read3']:
                            try:
                                MegaCom.closeDoor(globalVars['megaSer'], 2)
                                passedTrainingDoor = True
                                print("Mouse %s began training." % tracking)
                            except MegaCom.ServoError as e:
                                print("Unable to close door 2.")
                                passedTrainingDoor = False
                                continue
                    try:
                        compTimeObj = OpenMVCom.startRecording(camSer)
                    except Exception as e:
                        print('SerialException: OpenMV cam not connected.', e)
                    protocol = reportCards[tracking].currentProtocol
                    protocolModule = importlib.import_module('%s.%s' %(protocol,protocol))
                    print('%s beginning protocol "%s"' %(tracking, protocol))
                    try:
                        myBpod, reportCards[tracking] = protocolModule.runProtocol(bpodPort, reportCards[tracking])
                    except Exception as e:
                        print("Bpod exception:\n%s" %e)
                        AcademyUtils.resetBpodPort()
                    try:
                        actualStartTimeObj, endTimeObj, dur = OpenMVCom.stopRecording(camSer)
                    except Exception as e:
                        print('Camera failure:\n%s' %e)
                    #clear buffer 2 so we can read when
                    #training mouse passes reader 2
                    buff2 = MegaCom.clearBuffer(globalVars['megaSer'], 2)
                    print("Emptied buffer from reader 2:")
                    print(buff2)
                    MegaCom.openDoor(globalVars['megaSer'], 2)
                    exitedTraining = False
                    while not exitedTraining:
                        globalVars['tag2'] = MegaCom.readTag(globalVars['megaSer'], 2)
                        time.sleep(0.1)
                        globalVars['read2'] = MegaCom.isTag(globalVars['tag2'])
                        if globalVars['read2'] and tracking==tagIDtoSubject["id"][globalVars['tag2']]["mouseID"]:
                            exitedTraining = True
                            door2open = False
                            try:
                                MegaCom.closeDoor(globalVars['megaSer'], 2)
                                print("mouse %s exited training" % tracking)
                            except MegaCom.ServoError as e:
                                print("Unable to close door 2.")
                                exitedTraining = False
                                continue
                            print("Emptied buffer from reader 3:")
                            buff3 = MegaCom.clearBuffer(globalVars['megaSer'], 3)
                            print(buff3)
                            print("Emptied buffer from reader 1:")
                            buff1 = MegaCom.clearBuffer(globalVars['megaSer'], 1)
                            print(buff1)
                            try:
                                MegaCom.openDoor(globalVars['megaSer'], 1)
                            except MegaCom.ServoError:
                                globalVars['megaSer'] = MegaCom.resetMega()
                            returnedHome = False
                            while not returnedHome:
                                time.sleep(0.1)
                                globalVars['tag1'] = MegaCom.readTag(globalVars['megaSer'], 1)
                                if MegaCom.isTag(globalVars['tag1']) and tracking==tagIDtoSubject["id"][globalVars['tag1']]["mouseID"]:
                                    returnedHome = True
                                    buff2 = MegaCom.clearBuffer(globalVars['megaSer'], 2)
                                    print("mouse %s returned to home cage" % tracking)
            elapsed_time = time.time()-startTime
    

if __name__ == '__main__':
    main()
