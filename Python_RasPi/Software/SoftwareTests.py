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
import time
import serial
from serial.tools.list_ports_linux import comports
import AcademyUtils

def testAcademyUtils():
    try:
        import AcademyUtils
    except ImportError as e:
        raise AcademyUtilsError(e)
    
    modulesDir = AcademyUtils.getModulesDir()
    softwareDir = AcademyUtils.getSoftwareDir()
    rasPiDir = AcademyUtils.getRasPiDir()
    dataDir = AcademyUtils.getDataDir()
    calibrationDir = AcademyUtils.getCalibrationDir()
    reportCardDir = AcademyUtils.getReportCardDir()
    devices = AcademyUtils.getDevices()
    bpodUSBPort = AcademyUtils.findBpodUSBPort()
    bpodProgPort = AcademyUtils.findBpodProgPort()
    megaPort = AcademyUtils.findMegaPort()
    
    print('Modules:', modulesDir)
    print('Software:', softwareDir)
    print('Python_RasPi:', rasPiDir)
    print('Data:', dataDir)
    print('Calibration:', calibrationDir)
    print('ReportCards:', reportCardDir)
    print('Bpod USB Port:', bpodUSBPort)
    print('Bpod Prog Port:', bpodProgPort)
    print('Mega Port:', megaPort)
    AcademyUtils.printDevices()
    return True

def testReportCard():
    from ReportCardClass import ReportCard
    ds = ReportCard('DummySubject')
    ds.setCurrentProtocol('ProtocolTemplate')
    ds.save()
    
    return ds

def testBpodClass():
    from BpodClass import BpodObject
    bpodPort = AcademyUtils.findBpodUSBPort()
    myBpod = BpodObject(bpodPort)
    myBpod.set_subject('DummySubject')
    myBpod.disconnect()
    return None

def testProtocolTemplate():
    from ProtocolTemplate import ProtocolTemplate
    bpodPort = AcademyUtils.findBpodUSBPort()
    ds = testReportCard()
    myBpod, rc = ProtocolTemplate.runProtocol(bpodPort, ds)

def testCalibration():
    from Calibrate import Calibrate
    valveNum = 1
    pulseDuration = 60
    numPulses = 10

    calPath, pointDict = Calibrate.addPoint(valveNum, pulseDuration, numPulses)
    Calibrate.updatePoint(valveNum, calPath, pointDict)
    Calibrate.updateCoeffs(valveNum, calPath)
    return None

def testEnrollment():
    import RFID.Enrollment as Enrollment
    enrollmentSuccessful = Enrollment.main()
    if enrollmentSuccessful:
        print('Enrollment successful.')
    else:
        print('Enrollment unsuccessful.')
    return enrollmentSuccessful
        
def testRecord():
    import OpenMV.OpenMVCom as OpenMVCom
    movSecs = 3
    camSer, connected = OpenMVCom.connect()
    print('Connected:', connected)
    time.sleep(1)

    compTimeObj = OpenMVCom.startRecording(camSer)
    time.sleep(movSecs)
    actualStartTimeObj, endTimeObj, dur = OpenMVCom.stopRecording(camSer)
    print('Actual recording time: %d seconds.' % dur)
    OpenMVCom.disconnect(camSer)
    
class AcademyUtilsError(Exception):
    pass