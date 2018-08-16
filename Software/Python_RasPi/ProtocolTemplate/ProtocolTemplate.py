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
sys.path.append('/home/pi/Mouse_Academy/Software/Python_RasPi')
from Modules import BpodClass, StateMachineAssembler
import report_card as rc
import json

def main(argv):
    parser = argparse.ArgumentParser(description='Parse subject argument,')
    parser.add_argument('subject', metavar='S', type=str, nargs=1,
                        help='name of current animal (e.g. M0)')
    args = parser.parse_args()
    sub = args.subject[0]
    mouse = rc.ReportCard(sub)
    mouse.load()
    
    bpodPort = BpodUtils.findBpodPort()
                bpodPort = portName
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
    import numpy as np

    d = datetime.date.today()
    d.strftime("%b%d_%y")
    # Create a new instance of a Bpod object
    subject = reportCard.mouseID

    myBpod.set_subject(subject)
    maxWater = reportCard.maxWater
    rewardAmount = 4
    timeout = 5
    sessionDurationMinutes = 1
    
    LeftPort = int(1)
    CenterPort = int(2)
    RightPort = int(3)
    valveTimes = myBpod.getValveTimes(rewardAmount, [1, 2, 3])

    LeftValveTime = valveTimes[0]
    RightValveTime = valveTimes[2]
    CenterValveTime = valveTimes[1]

    LeftLED = 'PWM%d' % LeftPort
    CenterLED = 'PWM%d' % CenterPort
    RightLED = 'PWM%d' % RightPort
    LeftPortBin = 1
    CenterPortBin = 2
    RightPortBin = 4
    trialTypes = []
    myBpod.updateSettings({"Reward Amount": rewardAmount,
                           "Timeout": timeout,
                           "Session Duration (min)": sessionDurationMinutes})
    sc = myBpod.softCodeHandler
    
    currentTrial = 0
    exitPauseTime = 1
    
    sessionWater = 0
    maxWater = reportCard.maxWater
    waterToday = reportCard.getWaterToday()

    startTime = time.time()
    elapsed_time = 0
    
    while elapsed_time < sessionDurationMinutes*60:
        sma = stateMachine(myBpod) # Create a new state machine (events + outputs tailored for myBpod)
        #choose random decimal between 0 and 1
        randomDec = random.random()
        
        if randomDec > 0.5:
            trialType = 'Left'
        else:
            trialType = 'Right'
        #update list of trial types to save to file
        trialTypes = trialTypes + [trialType]
        print('Trial %d, %s' % (currentTrial, trialType))
        
        if trialType == 'HighLeft':
            leftCorrect = 'RewardLeft'
            rightCorrect = 'Timeout'
            displayLED = 'PWM1'
        else:
            leftCorrect = 'Timeout'
            rightCorrect = 'RewardRight'
            displayLED = 'PWM3'
            
        sma.addState('Name', 'WaitForPoke',
                     'Timer', 0,
                     'StateChangeConditions', ('Port1In', leftCorrect, 'Port3In', rightCorrect),
                     'OutputActions', (displayLED, 200))

        sma.addState('Name', 'RewardLeft',
                 'Timer', LeftValveTime,
                 'StateChangeConditions', ('Tup', 'ExitPause'),
                 'OutputActions', ('ValveState', 1))

        sma.addState('Name', 'RewardRight',
                 'Timer', RightValveTime,
                 'StateChangeConditions', ('Tup', 'ExitPause'),
                 'OutputActions', ('ValveState', 4))

        sma.addState('Name', 'Timeout',
                     'Timer', timeout,
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ())
                     
        sma.addState('Name', 'ExitPause',
                 'Timer', exitPauseTime,
                 'StateChangeConditions', ('Tup','exit'),
                 'OutputActions', ())
    
        
        myBpod.sendStateMachine(sma) # Send state machine description to Bpod device
        RawEvents = myBpod.runStateMachine() # Run state machine and return events
        myBpod.addTrialEvents(RawEvents)
        rawEventsDict = myBpod.structToDict(RawEvents)
        
        #Find reward times to update session water
        rewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, rewardState)
        rewarded = rewardTimes[0][0]>0
        
        #waterRewarded does not include click rewards
        if numConsecutiveCorrect == streak-1:
            waterReward = rewarded
        else:
            waterReward = 0
        print('correct:', rewarded)    
        print('waterReward:',waterReward)
        
        #if correct and water rewarded, update water and reset streak
        if waterReward:
            sessionWater += 0.001*rewardAmount
            if centerRewarded>0:
                sessionWater += 0.001*centerRewarded
            numConsecutiveCorrect = 0

        if rewarded:
            numConsecutiveCorrect += 1
            if trialType == 'HighLeft':
                leftPerf += 1
            elif trialType == 'LowRight':
                rightPerf += 1
            fractionLeftCorrect = leftPerf/(leftPerf+rightPerf)
        else:
            numConsecutiveCorrect = 0    
        
        elapsed_time = time.time()-startTime
        currentTrial = currentTrial+1
        
        if sessionWater+waterToday >= maxWater:
            print('reached maxWater (%d)' % maxWater)
            break
    print('Session water:', sessionWater)
    myBpod.updateSettings({'Trial Types':trialTypes})
    myBpod.saveSessionData()
    reportCard.drankWater(sessionWater, myBpod.currentDataFile)
    reportCard.save()
    # Disconnect Bpod
    myBpod.disconnect() # Sends a termination byte and closes the serial port. PulsePal stores current params to its EEPROM.
    sc.close()
    return myBpod, reportCard

if __name__ == "__main__":
    main(sys.argv[1:])

