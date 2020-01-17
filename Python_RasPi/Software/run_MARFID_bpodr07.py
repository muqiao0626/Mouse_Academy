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
from datetime import datetime
import json
import re
import serial
from serial.tools.list_ports_linux import comports
import importlib
import BpodClass
import AcademyUtils
import OpenMVClass
from OpenMVClass import OpenMVObject
from ReportCardClass import ReportCard
import MegaClass
from MegaClass import MegaObject


def main():
    systemFailure = False
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
    anyAllowed = False
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
        if rc.trainingAllowed:
            anyAllowed = True
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
        
    
    devices = AcademyUtils.getDevices()
    bpodPort = AcademyUtils.findBpodUSBPort(devices)
    megaPort = AcademyUtils.findMegaPort(devices)
    unoPort = AcademyUtils.findUnoPort(devices)
    devices.update({'Arduino Mega':megaPort})
    MegaCom = MegaObject(megaPort, unoPort)
    #AcademyUtils.resetBpodPort()
    
    tagIDtoSubject = AcademyUtils.getRoster()
    
        
    startTime = time.time()
    elapsed_time = 0
    
    try:
        OpenMVCom = OpenMVObject()
        useCam = True
    except Exception as e:
        print(e)
        useCam = False
        connected = [False]
        
    print("Connecting to %d OpenMV cam(s)" % OpenMVCom.numCams)

    idIn = ""

    MegaCom.openDoor(1)
    try:
        MegaCom.closeDoor(2)
    except:
        print('door 2 failed to close')
    MegaCom.closeDoor(2)
    while elapsed_time < 12*3600 and anyAllowed:
    #try readers 1 and 2 for tag
        tracking = None
        tag1 = MegaCom.readTag(1)
        time.sleep(0.1) #attempting to read tags too quickly causes
                        #errors in communicating with mega
        tag2 = MegaCom.readTag(2)
        time.sleep(0.1)
        read1 = MegaCom.isTag(tag1)
        read2 = MegaCom.isTag(tag2)
        #print('tag2: ', tag2)
        #print('read2: ', read2)
        if not read2:
            elapsed_time = time.time()-startTime  
        else: #wait for mouse to pass
            #find which mouse we're keeping track of
            tracking = tagIDtoSubject["id"][tag2]["mouseID"]
            #if animal is not allowed to train, wait for
            #animal to return to home cage, then clear buffers
            if not reportCards[tracking].trainingAllowed:
                print("Mouse %s not permitted to train." % tracking)
                returnedHome = False
                while not returnedHome:
                    tag1 = MegaCom.readTag(1)
                    time.sleep(0.05)
                    read1 = MegaCom.isTag(tag1)
                    if read1:
                        if tag1==reportCards[tracking].tagID:
                            returnedHome = True
                            print('Mouse %s returned to home cage' % tracking)
                            buff1 = MegaCom.clearBuffer(1)
                            buff2 = MegaCom.clearBuffer(2)
            #if animal is allowed to train:
            else:            
                #if not MegaCom.tag1InRange():
                if True:
                    print("Mouse %s passed checkpoint." % tracking)
                    try:
                        MegaCom.closeDoor(1)
                    except MegaCom.ServoError as e:
                        print("Door unable to close. Resetting reader buffers.")
                        buff1 = MegaCom.clearBuffer(1)
                        buff2 = MegaCom.clearBuffer(2)
                        continue
                    MegaCom.openDoor(2)
                    passedTrainingDoor = False
                    while not passedTrainingDoor:
                        tag3 = MegaCom.readTag(3)
                        time.sleep(0.1)
                        read3 = MegaCom.isTag(tag3)
                        if read3:
                            try:
                                MegaCom.closeDoor(2)
                                passedTrainingDoor = True
                                print("Mouse %s began training." % tracking)
                            except MegaCom.ServoError as e:
                                print("Unable to close door 2.")
                                passedTrainingDoor = False
                                continue
                    ##############################
                    #
                    # Turn on arena lights
                    #
                    ##############################
                    try:
                        MegaCom.turnLightsOn()
                    except Exception as e:
                        print(e)
                    
                    ##############################
                    #
                    # Start camera recordings
                    #
                    ##############################
                    if useCam:
                        try:
                            compTimeObjs = OpenMVCom.startRecordingAll()
                        except Exception as e:
                            print('SerialException: OpenMV cam not connected.', e)
                        
                    #############################
                    #
                    # Start Bpod protocol
                    #
                    #############################
                    protocol = reportCards[tracking].currentProtocol
                    protocolModule = importlib.import_module('%s.%s' %(protocol,protocol))
                    print('%s beginning protocol "%s"' %(tracking, protocol))
                    try:
                        if 'Bite' in protocol:
                            myBpod, reportCardUpdated, MegaCom = protocolModule.runProtocol(bpodPort, reportCards[tracking], megaObj=MegaCom)
                        
                        else:
                            myBpod, reportCardUpdated = protocolModule.runProtocol(bpodPort, reportCards[tracking])
                        reportCards.update({tracking:reportCardUpdated})
                    except Exception as e:
                        print(e)
                        try:
                            bpodPort = AcademyUtils.resetBpod(bpodUSBPort=bpodPort)
                        except Exception as e2:
                            print(e)
                            systemFailure = True
                            failtimeobj = datetime.fromtimestamp(time.time())
                            failtime = failtimeobj.strftime('%H:%M:%S')
                            print('Failed at %s.' %failtime)
                    #############################
                    #
                    # Stop camera recordings
                    #
                    #############################
                    if useCam:
                        try:
                            actualStartTimeObjs, endTimeObjs, durs = OpenMVCom.stopRecordingAll()
                        except Exception as e:
                            print(e)
                        
                    ##############################
                    #
                    # Turn off arena lights
                    #
                    ##############################
                    try:
                        MegaCom.turnLightsOff()
                    except Exception as e:
                        print(e)
                    #############################
                    #
                    # Wait for exit training
                    #
                    #############################
                    #clear buffer 2 so we can read when
                    #training mouse passes reader 2
                    buff2 = MegaCom.clearBuffer(2)
                    print("Emptied buffer from reader 2:")
                    print(buff2)
                    MegaCom.openDoor(2)
                    exitedTraining = False
                    while not exitedTraining:
                        tag2 = MegaCom.readTag(2)
                        time.sleep(0.1)
                        read2 = MegaCom.isTag(tag2)
                        if read2 and tracking==tagIDtoSubject["id"][tag2]["mouseID"]:
                            exitedTraining = True
                            door2open = False
                            try:
                                MegaCom.closeDoor(2)
                                print("mouse %s exited training" % tracking)
                            except MegaCom.ServoError as e:
                                print("Unable to close door 2.")
                                exitedTraining = False
                                continue
                            print("Emptied buffer from reader 3:")
                            buff3 = MegaCom.clearBuffer(3)
                            print(buff3)
                            print("Emptied buffer from reader 1:")
                            buff1 = MegaCom.clearBuffer(1)
                            print(buff1)
                            try:
                                MegaCom.openDoor(1)
                            except MegaCom.ServoError:
                                MegaCom.resetMega()
                            returnedHome = False
                            while not returnedHome:
                                time.sleep(0.1)
                                tag1 = MegaCom.readTag(1)
                                if MegaCom.isTag(tag1) and tracking==tagIDtoSubject["id"][tag1]["mouseID"]:
                                    returnedHome = True
                                    buff2 = MegaCom.clearBuffer(2)
                                    print("mouse %s returned to home cage" % tracking)
            elapsed_time = time.time()-startTime
            #check if any of the mice are still allowed to train for
            #the day. If so, continue main while loop
            #If not, break (and exit script)
            for key in reportCards.keys():

                anyAllowed = False
                if reportCards[key].trainingAllowed:
                    anyAllowed = True
                    break
            if systemFailure:
                anyAllowed = False
            if anyAllowed==False:
                try:
                    MegaCom.closeDoor(1)
                    if not systemFailure:
                        completeTime = time.time()
                        completeTimeObj = datetime.fromtimestamp(completeTime)
                        print("%s: All pupils have completed today's training!" %completeTimeObj.strftime('%H:%M:%S'))
        
                except MegaCom.ServoError as e:
                    failTime = time.time()
                    failTimeObj = datetime.fromtimestamp(failTime)
                    print("%s: System Failure." %failTimeObj.strftime('%H:%M:%S'))
                    print(e)
    

    

if __name__ == '__main__':
    main()
