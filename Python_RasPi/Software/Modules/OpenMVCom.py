import time
from datetime import datetime
import serial
import AcademyUtils
import sys

def connect():
    camPorts = AcademyUtils.getCamPorts()
    camSer = serial.Serial(camPorts[0], 9600, timeout=1)
    time.sleep(2)
    connectByte = camSer.read()
    connectMsg = int.from_bytes(connectByte, byteorder='little')
    if connectMsg == 1:
        connected = True
    else:
        connected = False
    return camSer, connected

def connectAll():
    camPorts = AcademyUtils.getCamPorts()
    numCams = len(camPorts)
    camSers = []
    connected = [False for x in range(numCams)]
    for camNum, camPort in enumerate(camPorts):
        camSers = camSers + [serial.Serial(camPort, 9600, timeout=1)]
        time.sleep(2)
        connectByte = camSers[camNum].read()
        connectMsg = int.from_bytes(connectByte, byteorder='little')
        if connectMsg == 1:
            connected[camNum] = True
    return camSers, connected

def disconnect(camSer):
    camSer.close()
    return True

def disconnectAll(camSers):
    for camSer in camSers:
        camSer.close()
    return True

##################################################
#
# OpenMV cam script requires start time as a byte
# array.
# compTime (13 bytes) - (current Unix time)*1000
#                       and truncated
##################################################
def startRecording(ser):
    nBytes = 13

    startTime = time.time()
    startTimeObj = datetime.fromtimestamp(startTime)
    compTime = int(1000*startTime)
    compTimeBytes = str(compTime)[0:nBytes].encode()
    ser.write(bytearray(compTimeBytes))
    print('Start Time: %s' %startTimeObj.strftime('%H:%M:%S'))
    return startTimeObj


def stopRecording(ser):
    ser.write('stop'.encode())
    actualStartTimeObj, endTimeObj = checkRecording(ser)
    
    actualDuration = (endTimeObj - actualStartTimeObj).total_seconds()
    return actualStartTimeObj, endTimeObj, actualDuration

def startRecordingAll(camSers):
    startTimeObjs = []
    for camSer in camSers:
        startTimeObj = startRecording(camSer)
        startTimeObjs = startTimeObjs + [startTimeObj]
        time.sleep(0.01)
        
    return startTimeObjs

def stopRecordingAll(camSers):
    actualStartTimeObjs = []
    endTimeObjs = []
    actualDurations = []
    for camSer in camSers:
        try:
            actualStartTimeObj, endTimeObj, actualDuration = stopRecording(camSer)
            actualStartTimeObjs = actualStartTimeObjs + [actualStartTimeObj]
            endTimeObjs = endTimeObjs + [endTimeObj]
            actualDurations = actualDurations + [actualDuration]
        
        except Exception as e:
            print('Camera failure:\n%s' %e)
        time.sleep(0.01)
    return actualStartTimeObjs, endTimeObjs, actualDurations
    



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
def checkRecording(ser):
    lines = ser.readlines()
    print(lines)
    if len(lines) <= 0:
        raise OpenMVError('Error: did not receive end of recording message from OpenMV Cam.')
    else:
        try:
            startEndBytes = lines[len(lines)-1]
            startEndStr = startEndBytes.decode()
            [startStr, endStr] = startEndStr.split(', ')
        except Exception as e:
            raise OpenMVError('Error: unable to parse end of recording message from OpenMV Cam:\n%s' %startEndStr)
        
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

if __name__ == '__main__':
    main()
