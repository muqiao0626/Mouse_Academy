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
    myBpod.set_protocol('HoldBite')
    import numpy as np

    d = datetime.date.today()
    d.strftime("%b%d_%y")
    # Create a new instance of a Bpod object
    subject = reportCard.mouseID

    myBpod.set_subject(subject)
    maxWater = reportCard.maxWater
    rewardAmount = 8
    sessionDurationMinutes = 3
    timeoutDur = 5
    maxHoldTime = 400
    holdTimes = [ht for ht in range(0, maxHoldTime+1, 25)]
    
    try:
        perfDictStr = reportCard.performance['HoldBite']
        perfDict = {}
        for htstr in list(perfDictStr.keys()):
            htint = int(htstr)
            perfDict[htint] = perfDictStr[htstr]
    except KeyError:
        reportCard.performance.update({'HoldBite':{}})
        perfDict = {ms:0 for ms in holdTimes}
        perfDictStr = {str(ms):0 for ms in holdTimes}
        reportCard.performance['HoldBite'].update(perfDictStr)
    #find hold time
    #(max hold time with performance > 70%)
    holdTime = 0
    htidx = 0
    if perfDict[maxHoldTime] > 0.70:
        holdTime = maxHoldTime
        reportCard.setCurrentProtocol('PatchBite')
    else:
        while perfDict[holdTime] > 0.70:
            htidx += 1
            holdTime = holdTimes[htidx]
    print('Hold Time:', holdTime)
    
    valveTimes = myBpod.getValveTimes(rewardAmount, [1])
    lickValveTime = valveTimes[0]
    
    CenterPort = int(2)
    CenterPortBin = 2
    valveTimes = myBpod.getValveTimes(rewardAmount, [CenterPort])
    centerValveTime = valveTimes[0]
    myBpod.updateSettings({"Reward Amount": rewardAmount,
                           "Hold Time (s)": holdTime,
                           "Timeout:":timeoutDur,
                           "Session Duration (min)": sessionDurationMinutes})
    
    currentTrial = 0
    exitPauseTime = 1
    
    sessionWater = 0
    maxWater = reportCard.maxWater
    waterToday = reportCard.getWaterToday()

    startTime = time.time()
    elapsed_time = 0
    trial = 1
    
    while elapsed_time < sessionDurationMinutes*60:
        print('Trial:', trial)
        sma = stateMachine(myBpod) 
        sma.addState('Name', 'WaitForBite',
                     'Timer', 0,
                     'StateChangeConditions', ('Wire1Out', 'Bitten'),
                     'OutputActions', ())
                     
        sma.addState('Name', 'Bitten',
                 'Timer', 0.001*holdTime,
                 'StateChangeConditions', ('Wire1In', 'EarlyRelease', 'Tup', 'WaitForRelease'),
                 'OutputActions', ('SoftCode', 1))
        sma.addState('Name', 'WaitForRelease',
                     'Timer', 5,
                     'StateChangeConditions', ('Wire1In', 'Released', 'Tup', 'Stuck'),
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
                     'Timer', centerValveTime,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('ValveState', CenterPortBin))
        sma.addState('Name', 'EarlyRelease',
                     'Timer', timeoutDur,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('SoftCode', 3))

    
        trial += 1        
        myBpod.sendStateMachine(sma) # Send state machine description to Bpod device
        RawEvents = myBpod.runStateMachine() # Run state machine and return events
        myBpod.addTrialEvents(RawEvents)
        elapsed_time = time.time() - startTime
        #Find reward times to update session water
        rewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, 'RewardBite')
        rewarded = rewardTimes[0][0]>0
        
        #if correct and water rewarded, update water and reset streak
        if rewarded:
            sessionWater += 0.001*rewardAmount
            

        elapsed_time = time.time()-startTime
        currentTrial = currentTrial+1
        
        if sessionWater+waterToday >= maxWater:
            print('reached maxWater (%d)' % maxWater)
            break
            
    print('Session water:', sessionWater)
    myBpod.saveSessionData()

    reportCard.drankWater(sessionWater, myBpod.currentDataFile)
    reportCard.save()
    # Disconnect Bpod
    myBpod.disconnect() # Sends a termination byte and closes the serial port. PulsePal stores current params to its EEPROM.
    return myBpod, reportCard

if __name__ == "__main__":
    main(sys.argv[1:])

