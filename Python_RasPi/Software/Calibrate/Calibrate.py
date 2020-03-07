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
import json
import numpy as np
from BpodClass import BpodObject
from StateMachineAssembler import stateMachine
import AcademyUtils

def addPoint(valveNum, pulseTime, numPulses):
    if numPulses > 200:
        print('Max number of pulses is 200; changing numPulses to 200.')
        numPulses = 200
    #from Bpod_Gen2.Python_3.Modules.BpodClass import BpodObject # Import BpodObject
    #from Bpod_Gen2_Python_3.Modules.StateMachineAssembler import stateMachine
    #import run_MARFID as rm
    pause = 0.3
    valveTime = pulseTime/1000
    valveBin = 2**(valveNum-1)
    # Find name of port
    portName = AcademyUtils.findBpodUSBPort()
    myBpod = BpodObject(portName)
    rc = myBpod.set_subject('Calibrator')
    rc.currentProtocol = 'Calibrate'
    calFolder = myBpod.calibrationFileFolder
    calFile = "valve_calibration_%d.json" % valveNum
    calPath = os.path.join(calFolder, calFile)
    for pulse in range(numPulses):
        sma = stateMachine(myBpod)
        sma.addState('Name', 'FirstPause',
                 'Timer', pause,
                 'StateChangeConditions', ('Tup', 'Pulse'),
                 'OutputActions', ())
        sma.addState('Name', 'Pulse',
                 'Timer', valveTime,
                 'StateChangeConditions', ('Tup', 'Pause'),
                 'OutputActions', ('ValveState', valveBin))
        sma.addState('Name', 'Pause',
                 'Timer', pause,
                 'StateChangeConditions', ('Tup', 'exit'),
                 'OutputActions', ())
        myBpod.sendStateMachine(sma)
        RawEvents = myBpod.runStateMachine()
        print('pulse:', pulse+1)
    myBpod.disconnect()

    vol = input('How many ml?')
    volume = float(vol)
    val = truncate(volume/numPulses, 4)
    pointDict = {str(float(pulseTime)):val}
    return calPath, pointDict

def updatePoint(valvenum, calFile, pointDict):
    if os.path.exists(calFile):
        f = open(calFile, 'r')
        s = f.read()
        f.close()
        calDict = json.loads(s)
        os.remove(calFile)
        f = open(calFile, 'w')
    else:
        import re
        f = open(calFile, 'w')
        valvebin = 2**(int(valvenum)-1)
        calDict = {"table":{}, "coeffs":[], "invcoeffs":[], "valve":str(valvebin)}

    calDict["table"].update(pointDict)
    f.write(json.dumps(calDict, indent=4))
    f.close()

def updateCoeffs(valvenum, calFile):
    if os.path.isfile(calFile):
        f = open(calFile, 'r')
        calDict = json.loads(f.read())
        f.close()
        if len(calDict["table"]) > 2:
            os.remove(calFile)
            f = open(calFile, 'w')
            calDict["table"].update({"0.0":"0.0"})
            xs = list(calDict["table"].keys())
            x = [float(i) for i in xs]
            y = [float(calDict["table"][str(val)])*1000 for val in x]
            coeffs = np.polyfit(x, y, 3)
            coeffs = [truncate(c, 7) for c in coeffs]
            calDict.update({"coeffs":list(coeffs)})

            invcoeffs = np.polyfit(y, x, 3)
            invcoeffs = [truncate(ic, 7) for ic in invcoeffs]
            calDict.update({"invcoeffs":list(invcoeffs)})
            f.write(json.dumps(calDict, indent=4))
            f.close()
            updatePlots(valvenum, calFile)
            return coeffs
        else:
            print('Please add more to calculate coefficients.')
            return None
    else:
        print('Calibration file does not exist.')
        return None
def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '%.12f' % f
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])
def updatePlots(valvenum, calFile):
    import matplotlib.pyplot as plt
    f = open(calFile, 'r')
    r = f.read()
    calDict = json.loads(r)
    f.close()
    pulseTimesStr = list(calDict["table"].keys())
    pulseVolsStr = [calDict["table"][p] for p in pulseTimesStr]
    pulseTimes = [float(x) for x in pulseTimesStr]
    pulseVols = [float(y)*1000 for y in pulseVolsStr]
    cs = calDict["coeffs"]
    coeffs = [float(c) for c in cs]
    p = np.poly1d(coeffs)
    polyx = [i*0.5 for i in range(0, 2*int(np.max(pulseTimes)))]
    polyy = np.polyval(p,polyx)
    lp = plt.plot(polyx, polyy, 'k')
    sc = plt.scatter(pulseTimes, pulseVols, 10)
    plt.xlabel('Time (ms)')
    plt.ylabel(r'Volume ($\mu$l)')
    plt.legend(['Fit', 'Calibration points'])
    plt.title("Valve %s" % valvenum)
    saveas = '.'.join([calFile.strip('.json'), 'pdf'])
    plt.savefig(saveas)

def main(argv):
    parser = argparse.ArgumentParser(description='Parse subject argument,')
    parser.add_argument('valvenum', metavar='V', type=str, nargs=1,
                        help='Valve number (1-8)')
    parser.add_argument('pulsetime', metavar='T', type=str, nargs=1,
                        help='Time of pulse in ms')
    parser.add_argument('numpulses', metavar='P', type=str, nargs=1,
                        help='number of pulses')
    args = parser.parse_args()
    vn = int(argv[0])
    pt = int(argv[1])
    nump = int(argv[2])

    calPath, pointDict = addPoint(vn, pt, nump)
    updatePoint(vn, calPath, pointDict)
    updateCoeffs(vn, calPath)

if __name__ == "__main__":
    main(sys.argv[1:])
