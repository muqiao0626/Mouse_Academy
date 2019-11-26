import time
from datetime import datetime
import serial
import AcademyUtils
import sys

class CameraObject(object):
    def __init__(self, portName, connect=True):
        self.baudrate = 115200
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.xonxoff = False
        self.rtscts = False
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1
        self.dsrdtr = True
        self.connected = False
        self.portName = portName
        self.serialObject = None
        self.startTimeObj = None
        self.endTimeObj = None
        self.isOpen = False
        self.isRecording = False
        
        if connect:
            self.serialObject = self.connect()
        
    def connect(self):
        self.serialObject = serial.Serial(self.portName,
                           baudrate=self.baudrate,
                           bytesize=self.bytesize,
                           parity=self.parity,
                           xonxoff=self.xonxoff,
                           rtscts=self.rtscts,
                           stopbits=self.stopbits,
                           timeout=self.timeout,
                           dsrdtr=self.dsrdtr)
        self.serialObject.setDTR(True)
        time.sleep(2)
        self.isOpen = True
        return self.serialObject
    
    def reconnect(self):
        self.serialObject.open()
        self.isOpen = self.serialObject.isOpen()
        return self.serialObject

    def disconnect(self):
        self.serialObject.close()
        self.isOpen = False
        return self.serialObject
        
    def reset(self):
        print('Resetting camera serial port %s...' %self.portName)
        if self.isOpen:
            self.disconnect()
        serObj = self.reconnect()
        return self


##################################################
#
# OpenMV cam script requires start time as a byte
# array.
# compTime (13 bytes) - (current Unix time)*1000
#                       and truncated
##################################################
    def startRecording(self):
        nBytes = 13

        startTime = time.time()
        startTimeObj = datetime.fromtimestamp(startTime)
        compTime = int(1000*startTime)
        compTimeBytes = str(compTime)[0:nBytes].encode()
        try:
            self.serialObject.write(bytearray(compTimeBytes))
            self.startTimeObj = startTimeObj
            print('Start Time: %s' %self.startTimeObj.strftime('%H:%M:%S'))
            self.isRecording = True
        except Exception as e:
            self.isRecording = False
            print('Start recording failed:')
            self.portName = None
            self.connected = False
            self.isOpen = False
            raise(OpenMVError(e))
        return startTimeObj


    def stopRecording(self):
        self.isRecording = False
        self.serialObject.write('stop'.encode())
        actualStartTimeObj, endTimeObj = self.checkRecording()
    
        self.lastDuration = (endTimeObj - actualStartTimeObj).total_seconds()
        return actualStartTimeObj, endTimeObj, self.lastDuration
    def readOutput(self):
        lines = self.serialObject.readlines(10)
        print(lines)

##################################################
#
# OpenMV cam script watches for stop message from
# computer then sends end message to computer:
# startEndStr (28 bytes) - actual start time
#                          (taking into account
#                          latency between record
#                          signal and actual
#                          recording)
#                        - end time of the video
#                          (calculated by cam)
#
##################################################
    def checkRecording(self):
        try:
            lines = self.serialObject.readlines()
        except Exception as e:
            print('Stop recording failed:')
            self.portName = None
            self.connected = False
            self.isOpen = False
            raise(OpenMVError(e))
        if len(lines) <= 0:
            raise OpenMVError('Error: did not receive end of recording message from OpenMV Cam.')
        else:
            try:
                startEndBytes = lines[len(lines)-1]
                startEndStr = startEndBytes.decode()
                [startStr, endStr] = startEndStr.split(', ')
            except Exception as e:
                raise OpenMVError('Error: unable to parse end of recording message from OpenMV Cam:\n%s' %lines)
        
            actualStartTime = int(startStr)
            endTime = int(endStr)
            actualStartTimeObj = datetime.fromtimestamp(0.001*actualStartTime)
            endTimeObj = datetime.fromtimestamp(0.001*endTime)
            print('Start Time: %s' %actualStartTimeObj.strftime('%H:%M:%S'))
            print('End Time: %s' %endTimeObj.strftime('%H:%M:%S'))
            actualDuration = 0.001*(endTime - actualStartTime)
            return actualStartTimeObj, endTimeObj
    
class OpenMVError(Exception):
    pass
