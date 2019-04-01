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
    myBpod.set_protocol('ProbLearn')
    import numpy as np

    d = datetime.date.today()
    d.strftime("%b%d_%y")
    # Create a new instance of a Bpod object
    subject = reportCard.mouseID

    myBpod.set_subject(subject)
    maxWater = reportCard.maxWater
    
    sessionDurationMinutes = 30
    
    minReward = 2
    maxReward = 8
    LeftPort = int(1)
    CenterPort = int(2)
    RightPort = int(3)
    minValveTimes = myBpod.getValveTimes(minReward, [LeftPort, CenterPort, RightPort])
    maxValveTimes = myBpod.getValveTimes(maxReward, [LeftPort, CenterPort, RightPort])
    valveTimes = {
        'Min':{
            'Left': minValveTimes[0],
            'Center': minValveTimes[1],
            'Right': minValveTimes[2],
            },
        'Max':{
            'Left': maxValveTimes[0],
            'Center': maxValveTimes[1],
            'Right': maxValveTimes[2],
            }
        }

    leftPortIn = 'Port%dIn' % LeftPort
    centerPortIn = 'Port%dIn' % CenterPort
    rightPortIn = 'Port%dIn' % RightPort
    leftPortBin = 1
    centerPortBin = 2
    rightPortBin = 4
    trialTypes = []
    highProb = 0.8
    lowProb = 0.4
    
    leftProb = lowProb
    rightProb = highProb
    rightRewardAmount = maxReward
    leftRewardAmount = maxReward
    
    myBpod.updateSettings({"Min Reward": minReward,
                           "Max Reward": maxReward,
                           "Left Reward": leftRewardAmount,
                           "Right Reward": rightRewardAmount,
                           "High Probability": highProb,
                           "Low Probability": lowProb,
                           "P(Left)": leftProb,
                           "P(Right)": rightProb,
                           "Left Amount (ul)": maxReward,
                           "Right Amount (ul)": maxReward,
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
        randNum = random.random() # generate random pause time between 100 and 1400 ms (10 ms step)
        if randNum < leftProb:
            leftReward = True
        else:
            leftReward = False
        if randNum < rightProb:
            rightReward = True
        else:
            rightReward = False
            
        if leftReward:
            rewardOrPauseLeft = 'RewardLeft'
        else:
            rewardOrPauseLeft = 'NoRewardLeft'
        if rightReward:
            rewardOrPauseRight = 'RewardRight'
        else:
            rewardOrPauseRight = 'NoRewardRight'
        sma = stateMachine(myBpod) # Create a new state machine (events + outputs tailored for myBpod)
        
        print('Trial %d' % currentTrial)
        print('Random Number:', randNum)
        print('Left Reward:', leftReward)
        print('Right Reward:', rightReward)
        
        sma.addState('Name', 'WaitForInit',
                     'Timer', 0,
                     'StateChangeConditions', (centerPortIn, 'WaitForChoice'),
                     'OutputActions', ())
        sma.addState('Name', 'WaitForChoice',
                     'Timer', 0,
                     'StateChangeConditions', (leftPortIn, rewardOrPauseLeft, rightPortIn, rewardOrPauseRight),
                     'OutputActions', ())

        sma.addState('Name', 'RewardLeft',
                 'Timer', valveTimes['Max']['Left'],
                 'StateChangeConditions', ('Tup', 'exit'),
                 'OutputActions', ('ValveState', leftPortBin))
        sma.addState('Name', 'NoRewardLeft',
                     'Timer', valveTimes['Max']['Left'],
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ())
        
        sma.addState('Name', 'RewardRight',
                 'Timer', valveTimes['Max']['Right'],
                 'StateChangeConditions', ('Tup', 'exit'),
                 'OutputActions', ('ValveState', rightPortBin))
        sma.addState('Name', 'NoRewardRight',
                     'Timer', valveTimes['Max']['Right'],
                     'StateChangeConditions', ('Tup', 'exit'),
                     'OutputActions', ())
    
        
        myBpod.sendStateMachine(sma) # Send state machine description to Bpod device
        RawEvents = myBpod.runStateMachine() # Run state machine and return events
        RawEvents.RandomNumber = []
        RawEvents.RandomNumber.append(randNum)
        myBpod.addTrialEvents(RawEvents)
        rawEventsDict = myBpod.structToDict(RawEvents)
        
        #Find reward times to update session water
        leftRewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, 'RewardLeft')
        rightRewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, 'RewardRight')
        rewardedLeft = leftRewardTimes[0][0]>0
        rewardedRight = rightRewardTimes[0][0]>0
        
        rewarded = False
        if rewardedLeft:
            rewarded = True
            print('Left Reward!')
        if rewardedRight:
            rewarded = True
            print('Right Reward!')


    #    try:
     #       withdrawalTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial].States, 'Withdrawal')
     #       withdrawal = withdrawalTimes[0][0]>0
     #   except AttributeError:
     #       withdrawal = False

        
        #if correct and water rewarded, update water and reset streak
        if rewardedLeft:
            sessionWater += 0.001*leftRewardAmount
        if rewardedRight:
            sessionWater += 0.001*rightRewardAmount

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

