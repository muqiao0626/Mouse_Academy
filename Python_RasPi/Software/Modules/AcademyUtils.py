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
import serial
import json
import time
from serial.tools.list_ports_linux import comports

def json_serial(obj):
    import datetime as dt
    if isinstance(obj, (dt.datetime, dt.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))
    
#find directories
def getModulesDir():
    modulesDir = os.path.dirname(os.path.realpath(__file__))
    return modulesDir

def getSoftwareDir():
    softwareDir = os.path.dirname(getModulesDir())
    return softwareDir

def getRasPiDir():
    rasPiDir = os.path.dirname(getSoftwareDir())
    return rasPiDir

def getDataDir():
    softwareDir = getSoftwareDir()
    dataDir = os.path.join(softwareDir, 'Data')
    return dataDir

def getCalibrationDir():
    calibrationDir = os.path.join(getSoftwareDir(), 'Calibrate')
    return calibrationDir

def getReportCardDir():
    reportCardDir = os.path.join(getDataDir(), 'ReportCards')
    return reportCardDir

def getRosterPath():
    rosterPath = os.path.join(getSoftwareDir(), 'RFID', 'Roster.json')
    if not os.path.isfile(rosterPath):
        emptyRoster = {'id':{}}
        with open(rosterPath, 'w') as f:
            f.write(json.dumps(emptyRoster, sort_keys=True, indent=2, separators=(',', ': '), default=json_serial))
    
    return rosterPath

def getRoster():
    rosterPath = getRosterPath()
    with open(rosterPath, 'r') as f:
        jsonstr = f.read()
        roster = json.loads(jsonstr)
    return roster

def getSubjectToTag():
    roster = getRoster()
    subToTag = {}
    for tag in roster['id']:
        subToTag[roster['id'][tag]['mouseID']] = tag
        
    return subToTag

def getDevices():
    iterator = sorted(comports())
    devices = {}
    for port in iterator:
        l = port[1].split(' (')
        portName = port[0]
        device = l[0].strip(')')
        devices.update({device:portName})
    return devices

def printDevices():
    devices = getDevices()
    print('Devices:')
    for device in devices:
        portname = devices[device]
        print('{}: {}'.format(device, portname))
    return devices

#Toggle DTR to reset serial port
def resetSer(ser):
    ser.setDTR(False)
    time.sleep(0.05)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.setDTR(True)

def findBpodUSBPort():
    foundBpodPort = False
    devices = getDevices()
    for device in devices:
        portname = devices[device]
        if 'Arduino Due' in device:
            if not 'Prog' in device:
                bpodPort = portname
                foundBpodPort = True
                break
    if foundBpodPort:
        return bpodPort
    else:
        raise DeviceError('Arduino Due Native USB Port not found.')
    
def resetBpodPort():
    bpodResetPort = findBpodProgPort()
    serial.Serial(bpodResetPort, 9600, timeout=0).close()
        
def getCamPort():
    foundCamPort = False
    devices = getDevices()
    for device in devices:
        portname = devices[device]
        if 'OpenMV' in device:
            camPort = portname
            foundCamPort = True
            break
    if foundCamPort:
        return camPort
    else:
        raise DeviceError('OpenMV Cam USB COM Port not connected.')
    
def findBpodProgPort():
    foundBpodPort = False
    devices = getDevices()
    for device in devices:
        portname = devices[device]
        if 'Arduino Due' in device:
            if 'Prog' in device:
                bpodPort = portname
                foundBpodPort = True
                break
    if foundBpodPort:
        return bpodPort
    else:
        raise DeviceError('Arduino Due Programming Port not found.')
    
#determine portname for arduino mega because it doesn't
#have a device name for some reason
def findMegaPort():
    devices = getDevices()
    megaFound = False
    print('Looking for Arduino Mega...')
    for key in devices.keys():
        if 'tty' in key:
            print('Trying port %s...' % devices[key])
            trySer = serial.Serial(devices[key], 9600, timeout=1)
            resetSer(trySer)
            r = trySer.readline()
            rline = r.decode().strip().lower()
            print("Message from serial device: %s" % rline)
            if 'mega' in rline:
                print('Arduino Mega 2560 found on port %s' % devices[key])
                trySer.readline()
                trySer.reset_output_buffer()
                trySer.reset_input_buffer()
                megaFound = True
                megaPort = devices[key]
                megaSer = trySer
                megaSer.close()
                break
            else:
                trySer.close()
    if not megaFound:
        raise DeviceError('Arduino Mega 2560 not found.')
    
    return devices[key]

class DeviceError(Exception):
    pass