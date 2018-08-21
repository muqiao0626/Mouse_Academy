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

def testBpodUtils():
    try:
        import BpodUtils
    except ImportError as e:
        raise BpodUtilsError(e)
    
    modulesDir = BpodUtils.getModulesDir()
    softwareDir = BpodUtils.getSoftwareDir()
    rasPiDir = BpodUtils.getRasPiDir()
    dataDir = BpodUtils.getDataDir()
    calibrationDir = BpodUtils.getCalibrationDir()
    reportCardDir = BpodUtils.getReportCardDir()
    devices = BpodUtils.getDevices()
    bpodUSBPort = BpodUtils.findBpodUSBPort()
    bpodProgPort = BpodUtils.findBpodProgPort()
    megaPort = BpodUtils.findMegaPort()
    
    print('Modules:', modulesDir)
    print('Software:', softwareDir)
    print('Python_RasPi:', rasPiDir)
    print('Data:', dataDir)
    print('Calibration:', calibrationDir)
    print('ReportCards:', reportCardDir)
    print('Bpod USB Port:', bpodUSBPort)
    print('Bpod Prog Port:', bpodProgPort)
    print('Mega Port:', megaPort)
    BpodUtils.printDevices()
    return True

def testReportCard():
    return None

def testBpodClass():
    return None

def testCalibration():
    return None

class BpodUtilsError(Exception):
    pass