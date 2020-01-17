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
from serial.tools.list_ports_linux import comports
from Modules import BpodClass, StateMachineAssembler, AcademyUtils, MegaClass
from ReportCardClass import ReportCard
import json

######################################################################
#
# Use to run protocol from command line
# e.g. ~$ python ProtocolTemplate/ProtocolTemplate.py 'Dummy Subject'
#
######################################################################
def main(argv):
    parser = argparse.ArgumentParser(description='Parse subject argument,')
    parser.add_argument('subject', metavar='S', type=str, nargs=1,
                        help='name of current animal (e.g. M0)')
    args = parser.parse_args()
    sub = args.subject[0]
    mouse = ReportCard(sub)
    mouse.load()

    bpodPort = AcademyUtils.findBpodUSBPort()

    myBpod, reportCard, megaObj = runProtocol(bpodPort, mouse)
    return myBpod, reportCard, megaObj


def runProtocol(bpodPort, reportCard, megaObj=None):
    # Initializing Bpod
    from BpodClass import BpodObject # Import BpodObject
    from MegaClass import MegaObject
    from StateMachineAssembler import stateMachine # Import state machine assembler
    import random
    import datetime
    import time
    # run_MARFID_bpodr07 passes megaObj
    if megaObj == None:
        passedMegaObj = False
        megaObj = MegaObject()
    else:
        passedMegaObj = True
    myBpod = BpodObject(bpodPort)
    myBpod.set_protocol('HoldBite')
    import numpy as np

    d = datetime.date.today()
    d.strftime("%b%d_%y")
    # Create a new instance of a Bpod object
    subject = reportCard.mouseID

    myBpod.set_subject(subject)
    maxWater = reportCard.maxWater
    rewardAmount = 4
    sessionDurationMinutes = .5
    biteEvent = 'Wire1In'
    releaseEvent='Wire1Out'
    timeoutDur = 0
    maxHoldTime = 400
    holdTimes = [ht for ht in range(0, maxHoldTime+1, 20)]

    if 'HoldBite' in reportCard.performance.keys():
        perfDictStr = reportCard.performance['HoldBite']
        perfDict = {}
        for htstr in list(perfDictStr.keys()):
            htint = int(htstr)
            perfDict[htint] = perfDictStr[htstr]
    else:
        reportCard.performance.update({'HoldBite':{}})
        perfDict = {ms:0 for ms in holdTimes}
        perfDictStr = {str(ms):0 for ms in holdTimes}
        reportCard.performance['HoldBite'].update(perfDictStr)
        reportCard.save()
    #find hold time
    #(max hold time with performance > minPerformance)
    minPerformance = 0.4
    holdTime = 0
    htidx = 0
    if perfDict[maxHoldTime] >= minPerformance:
        holdTime = maxHoldTime
        reportCard.setCurrentProtocol('HoldBite')
    else:
        completedHoldTime = True
        while completedHoldTime:
            try:
                completedHoldTime = perfDict[holdTime] > minPerformance
                if completedHoldTime:
                    htidx += 1
                    holdTime = holdTimes[htidx]
            except KeyError:
                perfDict.update({holdTime:0})
                perfDictStr.update({str(holdTime):0})
                reportCard.performance['HoldBite'].update(perfDictStr)
                reportCard.save()
                completedHoldTime = False
    print('Hold Time:', holdTime)
    print("RewardAmount: %s ul" % rewardAmount)

    
    LeftPort = int(1)
    LeftPortBin = 1
    valveTimes = myBpod.getValveTimes(rewardAmount, [LeftPort])
    leftValveTime = valveTimes[0]

    myBpod.updateSettings({"Reward Amount": rewardAmount,
                           "Hold Time (s)": holdTime,
                           "Timeout":timeoutDur,
                           "Session Duration (min)": sessionDurationMinutes,
                           "Bite Event": biteEvent,
                           "Release Event": releaseEvent})

    currentTrial = 0
    exitPauseTime = 1

    sessionWater = 0
    maxWater = reportCard.maxWater
    waterToday = reportCard.getWaterToday()
    numRewards = 0

    try:
        megaObj.beginLogging()
    except Exception as e:
        print('could not begin logging', e)
        print('Resetting uno...')
        try:
            megaObj = megaObj.resetUno()
            megaObj.beginLogging()
        except Exception as e2:
            print(e2)

    startTime = time.time()
    elapsed_time = 0
    trial = 1

    while elapsed_time < sessionDurationMinutes*60:
        print('Trial:', trial)
        sma = stateMachine(myBpod)
        sma.addState('Name', 'WaitForBite',
                     'Timer', 0,
                     'StateChangeConditions', (biteEvent, 'Bitten'),
                     'OutputActions', ())

        sma.addState('Name', 'Bitten',
                 'Timer', 0.001*holdTime,
                 'StateChangeConditions', (releaseEvent, 'EarlyRelease', 'Tup', 'WaitForRelease'),
                 'OutputActions', ('SoftCode', 1))
        sma.addState('Name', 'WaitForRelease',
                     'Timer', 5,
                     'StateChangeConditions', (releaseEvent, 'Released', 'Tup', 'Stuck'),
                     'OutputActions', ())
        sma.addState('Name', 'Stuck',
                     'Timer', 0.01,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('SoftCode', 4))
        sma.addState('Name', 'Released',
                 'Timer', 0,
                 'StateChangeConditions', ('Tup','RewardBite'),
                 'OutputActions', ('SoftCode', 2))
        sma.addState('Name', 'RewardBite',
                     'Timer', leftValveTime,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('ValveState', LeftPortBin))
        sma.addState('Name', 'EarlyRelease',
                     'Timer', timeoutDur,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('SoftCode', 3, 'Wire1', 1))


        trial += 1
        try:
            myBpod.sendStateMachine(sma) # Send state machine description to Bpod device
        except Exception as e:
            print(e)
            print("adjusting session duration...")
            sessionDurationMinutes = 0.01*int(100*(time.time() - startTime)/60)
            myBpod.updateSettings({"Session Duration (min)": sessionDurationMinutes})
        try:
            RawEvents = myBpod.runStateMachine() # Run state machine and return events
            myBpod.addTrialEvents(RawEvents)
            elapsed_time = time.time() - startTime
            #Find reward times to update session water
            rewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, 'RewardBite')
            rewarded = rewardTimes[0][0]>0
        
            #if correct and water rewarded, update water and reset streak
            if rewarded:
                numRewards += 1
                sessionWater += 0.001*rewardAmount
            

            elapsed_time = time.time()-startTime
            currentTrial = currentTrial+1
        
            if sessionWater+waterToday >= maxWater:
                print('reached maxWater (%f)' % maxWater)
                break
        except Exception as e:
            print(e)
            print('Exiting protocol...')

            break

    print('Session water:', sessionWater)
    myBpod.saveSessionData()

    actualTrials = currentTrial
    performance = numRewards/actualTrials
    print('%d rewards in %d trials (%.02f)' % (numRewards, actualTrials, performance))
    if currentTrial >=30:
        perfDictStr.update({str(holdTime):performance})

    reportCard.performance['HoldBite'].update(perfDictStr)
    reportCard.drankWater(sessionWater, myBpod.currentDataFile)
    reportCard.save()
    # Disconnect Bpod
    # Sends a termination byte and closes the serial port.
    # PulsePal stores current params to its EEPROM.
    myBpod.disconnect()

    # Send two termination bytes to bite logging arduino
    if megaObj.isLogging:
        megaObj.endLogging()

    # if this protocol not called from run_MARFID, disconnect mega
    if not passedMegaObj:
        megaObj.disconnect()
    return myBpod, reportCard, megaObj

if __name__ == "__main__":
    main(sys.argv[1:])
