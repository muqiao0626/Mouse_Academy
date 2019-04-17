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
    myBpod.set_protocol('ProbBlocks')
    import numpy as np

    d = datetime.date.today()
    d.strftime("%b%d_%y")
    # Create a new instance of a Bpod object
    subject = reportCard.mouseID

    myBpod.set_subject(subject)
    maxWater = reportCard.maxWater
    
    sessionDurationMinutes = 10
    
    minReward = 2
    maxReward = 4
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
    
    rightRewardAmount = maxReward
    leftRewardAmount = maxReward
    
    # decide number of trials per block
    numBlocks = 30
    blockLengthsLong = [random.randrange(40, 81, 1) for r in range(numBlocks)]
    pairs = list(set(["10:50", "10:90", "50:10", "50:50", "50:90", "90:50", "90:10"]))

    # choose block types without having same block
    # back-to-back
    oldBlockType = random.choice(pairs)
    blockTypesLong = [oldBlockType for b in range(numBlocks)]
    for b in range(numBlocks-1):
        newBlockType = random.choice(pairs)
        while oldBlockType == newBlockType:
            newBlockType = random.choice(pairs)
        oldBlockType = newBlockType
        blockTypesLong[b+1] = newBlockType

    # generate random numbers for each trial
    numTrialsLong = sum(blockLengthsLong)
    randNumsLong = [random.random() for t in range(numTrialsLong)]

    # find L/R probabilities for each block
    leftProbBlocksLong = [0.01*int(b.split(':')[0]) for b in blockTypesLong]
    rightProbBlocksLong = [0.01*int(b.split(':')[1]) for b in blockTypesLong]

    # find trial types
    leftRewardsLong = [False for t in range(numTrialsLong)]
    rightRewardsLong = [False for t in range(numTrialsLong)]

    btrial = 0
    blockIdx = 0
    trial = 0
    for blockLength in blockLengthsLong:
        while btrial < blockLength:
            #print('BlockIdx:', blockIdx, 'BlockLength:', blockLength, ', BlockType:', blockTypesLong[blockIdx], ', Trial:', trial)
            if randNumsLong[trial]<leftProbBlocksLong[blockIdx]:
                leftRewardsLong[trial] = True
            if randNumsLong[trial]<rightProbBlocksLong[blockIdx]:
                rightRewardsLong[trial] = True
            #print('randNum:', randNumsLong[trial])
            #print('left reward:', leftRewardsLong[trial])
            #print('right reward:', rightRewardsLong[trial])
            btrial += 1
            trial += 1
        blockIdx += 1
        btrial = 0


    myBpod.updateSettings({
                           "Left Amount (ul)": leftRewardAmount,
                           "Right Amount (ul)": rightRewardAmount,
                           "Session Duration (min)": sessionDurationMinutes
                           })
    
    currentTrial = 1
    exitPauseTime = 2
    
    sessionWater = 0
    maxWater = reportCard.maxWater
    waterToday = reportCard.getWaterToday()
    withdrawal = True

    startTime = time.time()
    elapsed_time = 0
    
    while elapsed_time < sessionDurationMinutes*60 and currentTrial < numTrialsLong:
    
        if leftRewardsLong[currentTrial-1]:
            rewardOrPauseLeft = 'RewardLeft'
        else:
            rewardOrPauseLeft = 'NoRewardLeft'
        if rightRewardsLong[currentTrial-1]:
            rewardOrPauseRight = 'RewardRight'
        else:
            rewardOrPauseRight = 'NoRewardRight'
        sma = stateMachine(myBpod) # Create a new state machine (events + outputs tailored for myBpod)
        
        print('Trial %d' % currentTrial)
        print('Random Number:', randNumsLong[currentTrial-1])
        print('Left Reward:', leftRewardsLong[currentTrial-1])
        print('Right Reward:', rightRewardsLong[currentTrial-1])
        
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

        myBpod.addTrialEvents(RawEvents)
        rawEventsDict = myBpod.structToDict(RawEvents)
        
        #Find reward times to update session water
        leftRewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial-1].States, 'RewardLeft')
        rightRewardTimes = getattr(myBpod.data.rawEvents.Trial[currentTrial-1].States, 'RewardRight')
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
    reportCard.drankWater(sessionWater, myBpod.currentDataFile)
    reportCard.save()
    # shorten lists to actual # trials
    actualTrials = currentTrial
    leftRewards = leftRewardsLong[0:actualTrials]
    rightRewards = rightRewardsLong[0:actualTrials]
    # find actual blockLengths
    hitBlocks = np.cumsum(blockLengthsLong)<actualTrials
    actualBlocks = sum(hitBlocks)+1
    c = np.cumsum(blockLengthsLong[0:actualBlocks])
    # find number of trials to slice off last (unfinished) block
    numSlice = c[len(c)-1] - actualTrials
    blockLengths = blockLengthsLong[0:actualBlocks]
    blockLengths[actualBlocks-1] = blockLengthsLong[actualBlocks-1] - numSlice
    myBpod.updateSettings({
                            "Left Rewards":list(leftRewards),
                            "Right Rewards":list(rightRewards),
                            "nTrials": actualTrials,
                            "Block Lengths": [int(bl) for bl in blockLengths],
                            "Random Numbers": list(randNumsLong[0:actualTrials]),
                            "Block Types": list(blockTypesLong[0:actualBlocks])
                          })
    myBpod.saveSessionData()
    # Disconnect Bpod
    myBpod.disconnect() # Sends a termination byte and closes the serial port. PulsePal stores current params to its EEPROM.
    return myBpod, reportCard

if __name__ == "__main__":
    main(sys.argv[1:])

