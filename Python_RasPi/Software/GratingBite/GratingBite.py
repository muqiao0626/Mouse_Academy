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
    myBpod.set_protocol('GratingBite')
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
    timeoutDur = 2
    maxDelayTime = 1200
    minDelayTime = 20
    gratingSize = 15
    possibleDelayTimes = [pd for pd in range(0, maxDelayTime+1, 20)]

    if 'GratingBite' in reportCard.performance.keys():
        perfDictStr = reportCard.performance['GratingBite']
        perfDict = {}
        for pdstr in list(perfDictStr.keys()):
            pdint = int(pdstr)
            perfDict[pdint] = perfDictStr[pdstr]
    else:
        reportCard.performance.update({'GratingBite':{}})
        perfDict = {ms:0 for ms in possibleDelayTimes}
        perfDictStr = {str(ms):0 for ms in possibleDelayTimes}
        reportCard.performance['GratingBite'].update(perfDictStr)
        reportCard.save()
    #find hold time
    #(max hold time with performance > minPerformance)
    minPerformance = 0.7
    delayMax = 0
    dmidx = 0
    if perfDict[maxDelayTime] >= minPerformance:
        delayMax = maxDelayTime
        reportCard.setCurrentProtocol('GratingBite')
    else:
        completedMaxDelay = True
        while completedMaxDelay:
            try:
                completedMaxDelay = perfDict[delayMax] > minPerformance
                if completedHoldTime:
                    dmidx += 1
                    delayMax = possibleDelayTimes[dmidx]
            except KeyError:
                perfDict.update({delayMax:0})
                perfDictStr.update({str(delayMax):0})
                reportCard.performance['GratingBite'].update(perfDictStr)
                reportCard.save()
                completedMaxDelay = False
    print('Max Delay:', delayMax)
    print("RewardAmount: %s ul" % rewardAmount)

    
    LeftPort = int(1)
    LeftPortBin = 1
    valveTimes = myBpod.getValveTimes(rewardAmount, [LeftPort])
    leftValveTime = valveTimes[0]
    
    gratingAngles = [0, 90]
    angleCodes = [2, 3]
    codeDict = {2:0, 3:90}

    myBpod.updateSettings({"Reward Amount": rewardAmount,
                           "Hold Time (s)": holdTime,
                           "Timeout":timeoutDur,
                           "Min Delay":minDelayTime,
                           "Max Delay": delayMax,
                           "Grating Size": gratingSize,
                           "Response Window": responseWindow,
                           "Grating Angles": gratingAngles,
                           "Session Duration (min)": sessionDurationMinutes,
                           "Bite Event": biteEvent,
                           "Release Event": releaseEvent})

    currentTrial = 0
    exitPauseTime = 1
    flipDelay = 0.121

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
    angles = []
    startTime = time.time()
    elapsed_time = 0
    trial = 1

    while elapsed_time < sessionDurationMinutes*60:
        vptime = 0.001*random.randrange(0, delayMax, 10) # generate random pause time between min and max delays (10 ms step)
        softByte = random.choice(angleCodes)
        print('Trial:', trial)
        sma = stateMachine(myBpod)
        sma.addState('Name', 'WaitForBite',
                     'Timer', 0,
                     'StateChangeConditions', (biteEvent, 'VariablePause'),
                     'OutputActions', ())
            
        sma.addState('Name', 'VariablePause',
                     'Timer', delayTime,
                     'StateChangeConditions', ('Tup', 'Display', releaseEvent, 'EarlyRelease'),
                     'OutputActions', ('SoftCode', 1))
        
        sma.addState('Name', 'EarlyRelease',
                     'Timer', timeout,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('SoftCode', 5))
        
        sma.addState('Name', 'Display',
                     'Timer', flipDelay,
                     'StateChangeConditions', (releaseEvent, 'EarlyRelease', 'Tup', 'WaitForRelease'),
                     'OutputActions', ('SoftCode', softByte))
        
        sma.addState('Name', 'WaitForRelease',
                     'Timer', responseWindowSecs,
                     'StateChangeConditions', (releaseEvent, 'Reward', 'Tup', 'Miss'),
                     'OutputActions', ())

        sma.addState('Name', 'Reward',
                 'Timer', leftValveTime,
                 'StateChangeConditions', ('Tup', 'exit'),
                 'OutputActions', ('ValveState', LeftPortBin, 'SoftCode', 4))
        sma.addState('Name', 'Miss',
                     'Timer', timeout,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('SoftCode', 5))
        

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
            RawEvents.GratingFlipTime = []
            RawEvents.GratingFlipTime.append(myBpod.softCodeHandler.gratingFlip)
            RawEvents.GrayFlipTime = []
            RawEvents.GrayFlipTime.append(myBpod.softCodeHandler.grayFlip)
            RawEvents.WhiteFlipTime = []
            RawEvents.WhiteFlipTime.append(myBpod.softCodeHandler.whiteFlip)
            RawEvents.Angle = []
            RawEvents.Angle.append(codeDict[softByte]])
            RawEvents.Delay = []
            RawEvents.Delay.append(vptime)
            myBpod.addTrialEvents(RawEvents)
            elapsed_time = time.time() - startTime
            #Find reward times to update session water
            rewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, 'Reward')
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
        perfDictStr.update({str(delayMax):performance})

    reportCard.performance['GratingBite'].update(perfDictStr)
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
