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
    myBpod.set_protocol('PatchLick')
    import numpy as np

    d = datetime.date.today()
    d.strftime("%b%d_%y")
    # Create a new instance of a Bpod object
    subject = reportCard.mouseID

    myBpod.set_subject(subject)
    maxWater = reportCard.maxWater
    rewardAmount = 4
    timeout = 8
    sessionDurationMinutes = 0.08
    responseWindow = 700#in ms
    responseWindowSecs = 0.001*responseWindow
    
    LeftPort = int(1)
    CenterPort = int(2)
    RightPort = int(3)
    valveTimes = myBpod.getValveTimes(rewardAmount, [2])

    CenterValveTime = valveTimes[0]

    LeftLED = 'PWM%d' % LeftPort
    CenterLED = 'PWM%d' % CenterPort
    RightLED = 'PWM%d' % RightPort
    LeftPortBin = 1
    CenterPortBin = 2
    RightPortBin = 4
    trialTypes = []
    minDelay = 700
    maxDelay = 3000
    patchSize = 25
    flipDelay = 0.121
    myBpod.updateSettings({"Reward Amount": rewardAmount,
                           "Timeout": timeout,
                           "Min Delay":minDelay,
                           "Max Delay": maxDelay,
                           "Patch Size": patchSize,
                           "Response Window": responseWindow,
                           "Session Duration (min)": sessionDurationMinutes})
    
    currentTrial = 0
    exitPauseTime = 2
    
    sessionWater = 0
    maxWater = reportCard.maxWater
    waterToday = reportCard.getWaterToday()
    withdrawal = True

    startTime = time.time()
    elapsed_time = 0
    
    while elapsed_time < sessionDurationMinutes*60:
        vptime = 0.001*random.randrange(minDelay, maxDelay, 10) # generate random pause time between 100 and 1400 ms (10 ms step)
        sma = stateMachine(myBpod) # Create a new state machine (events + outputs tailored for myBpod)
        
        print('Trial %d' % currentTrial)
##        if withdrawal:
        delayTime = vptime #+ 2 #penalty for withdrawal
        sma.addState('Name', 'WaitForInit',
                     'Timer', 0,
                     'StateChangeConditions', ('Port1In', 'VariablePause', 'Port1Out', 'Withdrawal'),
                     'OutputActions', ())
##        else:
##            delayTime = vptime
##            sma.addState('Name', 'WaitForInit',
##                         'Timer', 0.01,
##                         'StateChangeConditions', ('Tup', 'VariablePause', 'Port1Out', 'Withdrawal'),
##                         'OutputActions', ())
            
        sma.addState('Name', 'VariablePause',
                     'Timer', delayTime,
                     'StateChangeConditions', ('Tup', 'Display', 'Port1Out', 'Withdrawal', 'Port2In', 'FalseStart'),
                     'OutputActions', ())
        
        sma.addState('Name', 'FalseStart',
                     'Timer', timeout,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('SoftCode', 2))
        
        sma.addState('Name', 'Display',
                     'Timer', flipDelay,
                     'StateChangeConditions', ('Port2In', 'FalseStart', 'Port1Out', 'Withdrawal', 'Tup', 'WaitForLick'),
                     'OutputActions', ('SoftCode', 1))
        
        sma.addState('Name', 'WaitForLick',
                     'Timer', responseWindowSecs,
                     'StateChangeConditions', ('Port2In', 'RewardLick', 'Port1Out', 'Withdrawal', 'Tup', 'Miss'),
                     'OutputActions', ())

        sma.addState('Name', 'RewardLick',
                 'Timer', CenterValveTime,
                 'StateChangeConditions', ('Tup', 'Drinking'),
                 'OutputActions', ('ValveState', 2, 'SoftCode', 2))
        sma.addState('Name', 'Drinking',
                     'Timer', 0,
                     'StateChangeConditions', ('Port1Out', 'exit'),
                     'OutputActions', ())
        sma.addState('Name', 'Miss',
                     'Timer', timeout,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('SoftCode', 2))
        sma.addState('Name', 'Withdrawal',
                     'Timer', 0,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ('SoftCode', 2))
    
        
        myBpod.sendStateMachine(sma) # Send state machine description to Bpod device
        RawEvents = myBpod.runStateMachine() # Run state machine and return events
        RawEvents.PatchFlipTime = []
        RawEvents.PatchFlipTime.append(myBpod.softCodeHandler.patchFlip)
        RawEvents.BlackFlipTime = []
        RawEvents.BlackFlipTime.append(myBpod.softCodeHandler.blackFlip)
        RawEvents.Delay = []
        RawEvents.Delay.append(vptime)
        myBpod.addTrialEvents(RawEvents)
        rawEventsDict = myBpod.structToDict(RawEvents)
        myBpod.softCodeHandler.clearFlipTimes()
        
        #Find reward times to update session water
        rewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, 'RewardLick')
        rewarded = rewardTimes[0][0]>0


        try:
            withdrawalTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, 'Withdrawal')
            withdrawal = withdrawalTimes[0][0]>0
        except AttributeError:
            withdrawal = False

        
        #if correct and water rewarded, update water and reset streak
        if rewarded:
            sessionWater += 0.001*rewardAmount

        elapsed_time = time.time()-startTime
        currentTrial = currentTrial+1
        
        if sessionWater+waterToday >= maxWater:
            print('reached maxWater (%d)' % maxWater)
            break
            
    myBpod.softCodeHandler.close()
    print('Session water:', sessionWater)
    myBpod.updateSettings({'Trial Types':trialTypes})
    myBpod.saveSessionData()
    reportCard.drankWater(sessionWater, myBpod.currentDataFile)
    reportCard.save()
    # Disconnect Bpod
    myBpod.disconnect() # Sends a termination byte and closes the serial port. PulsePal stores current params to its EEPROM.
    return myBpod, reportCard

if __name__ == "__main__":
    main(sys.argv[1:])

