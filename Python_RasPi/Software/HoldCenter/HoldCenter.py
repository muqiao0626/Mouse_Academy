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
from Modules import BpodClass, StateMachineAssembler, AcademyUtils
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
    myBpod, reportCard = runProtocol(bpodPort, mouse)
    return myBpod, reportCard
                
def runProtocol(bpodPort, reportCard):
    # Initializing Bpod
    from BpodClass import BpodObject # Import BpodObject
    from StateMachineAssembler import stateMachine # Import state machine assembler
    import random
    import datetime
    import time
    myBpod = BpodObject(bpodPort)
    myBpod.set_protocol('HoldCenter')
    import numpy as np

    d = datetime.date.today()
    d.strftime("%b%d_%y")
    # Create a new instance of a Bpod object
    subject = reportCard.mouseID

    myBpod.set_subject(subject)
    maxWater = reportCard.maxWater
    minPerformance = 0.7
    timeout = 0.1
    maxHoldTime = 400
    holdTimes = [ht for ht in range(0, maxHoldTime+1, 25)]
    
    try:
        perfDictStr = reportCard.performance['HoldCenter']
        perfDict = {}
        for htstr in list(perfDictStr.keys()):
            htint = int(htstr)
            perfDict[htint] = perfDictStr[htstr]
    except KeyError:
        reportCard.performance.update({'HoldCenter':{}})
        perfDict = {ms:0 for ms in holdTimes}
        perfDictStr = {str(ms):0 for ms in holdTimes}
        reportCard.performance['HoldCenter'].update(perfDictStr)
    #find hold time
    #(max hold time with performance > 70%)
    holdTime = 0
    htidx = 0
    if perfDict[maxHoldTime] > minPerformance:
        holdTime = maxHoldTime
        reportCard.setCurrentProtocol('HoldCenterLRProbs')
    else:
        while perfDict[holdTime] > minPerformance:
            htidx += 1
            holdTime = holdTimes[htidx]
    print('Hold Time:', holdTime) 
 
    sessionDurationMinutes = 5
    rewardAmount = 1
    LeftPort = int(1)
    CenterPort = int(2)
    RightPort = int(3)
    valveTimes = myBpod.getValveTimes(rewardAmount, [LeftPort, CenterPort, RightPort])
    leftPortIn = 'Port%dIn' % LeftPort
    centerPortIn = 'Port%dIn' % CenterPort
    centerPortOut = 'Port%dOut' % CenterPort
    rightPortIn = 'Port%dIn' % RightPort
    leftPortBin = 1
    centerPortBin = 2
    rightPortBin = 4
    centerValveTime = valveTimes[1]
    

    myBpod.updateSettings({
                           "Reward Amount (ul)": rewardAmount,
                           "Timeout (s)": timeout,
                           "Hold Time (ms)": holdTime,
                           "Session Duration (min)": sessionDurationMinutes
                           })
    
    currentTrial = 1
    exitPauseTime = 1
    
    sessionWater = 0
    numRewards = 0
    maxWater = reportCard.maxWater
    waterToday = reportCard.getWaterToday()
    withdrawal = True

    startTime = time.time()
    elapsed_time = 0
    
    while elapsed_time < sessionDurationMinutes*60:
    
        sma = stateMachine(myBpod) # Create a new state machine (events + outputs tailored for myBpod)
        
        print('Trial %d' % currentTrial)
        
        sma.addState('Name', 'WaitForPoke',
                     'Timer', 0,
                     'StateChangeConditions', (centerPortIn, 'Poked'),
                     'OutputActions', ())
        
        sma.addState('Name', 'Poked',
                     'Timer', 0.001*holdTime,
                     'StateChangeConditions', ('Tup', 'RewardCenter', centerPortOut, 'EarlyRelease'),
                     'OutputActions', ())
        
        sma.addState('Name', 'EarlyRelease',
                     'Timer', timeout,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ())
        
        sma.addState('Name', 'RewardCenter',
                 'Timer', valveTimes[1],
                 'StateChangeConditions', ('Tup', 'ExitPause'),
                 'OutputActions', ('ValveState', centerPortBin))
        
        sma.addState('Name', 'ExitPause',
                     'Timer', exitPauseTime,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ())
    
        try:
            myBpod.sendStateMachine(sma) # Send state machine description to Bpod device
            RawEvents = myBpod.runStateMachine() # Run state machine and return events
        except Exception as e:
            print(e)
            sessionDurationMinutes = 0.01*int(100*(time.time()-startTime)/60)
            myBpod.updateSettings({
                           "Session Duration (min)": sessionDurationMinutes
                           })
            break

        myBpod.addTrialEvents(RawEvents)
        rawEventsDict = myBpod.structToDict(RawEvents)
        
        #Find reward times to update session water
        rewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial-1].States, 'RewardCenter')
        rewarded = rewardTimes[0][0]>0
        
        #if correct and water rewarded, update water and reset streak
        if rewarded:
            sessionWater += 0.001*rewardAmount
            numRewards += 1

        elapsed_time = time.time()-startTime
        currentTrial = currentTrial+1
        
        if sessionWater+waterToday >= maxWater:
            print('reached maxWater (%f)' % maxWater)
            break
            
    print('Session water:', sessionWater)
    actualTrials = currentTrial-1
    performance = numRewards/actualTrials
    print('%d rewards in %d trials (%.02f)' % (numRewards, actualTrials, performance))
    if currentTrial >=30:
        perfDictStr.update({str(holdTime):performance})
                
    reportCard.performance['HoldCenter'].update(perfDictStr)
    if perfDict[maxHoldTime] > minPerformance:
        reportCard.setCurrentProtocol('HoldCenterLRProbs')
    reportCard.drankWater(sessionWater, myBpod.currentDataFile)
    reportCard.save()
    myBpod.updateSettings({
                            "Rewards":numRewards,
                            "nTrials": actualTrials})
    myBpod.saveSessionData()
    # Disconnect Bpod
    myBpod.disconnect() # Sends a termination byte and closes the serial port. PulsePal stores current params to its EEPROM.
    return myBpod, reportCard

if __name__ == "__main__":
    main(sys.argv[1:])

