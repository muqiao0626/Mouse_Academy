import time
from datetime import datetime
from CameraClass import CameraObject
from CameraClass import OpenMVError
import serial
import AcademyUtils
import sys

class OpenMVObject(object):
    def __init__(self, portNames=[], connectAll=True):
        self.connected = []
        
        if len(portNames)<1:
            portNames = AcademyUtils.getCamPorts()
        self.camPorts = portNames
        if isinstance(self.camPorts, str):
            self.camPorts = list(self.camPorts)
        self.numCams = len(self.camPorts)
        self.camObjects = []
        if connectAll:
            self.camObjects = self.connectAll()
        self.portNames = portNames
        
    def connectAll(self):
        camObjs = []
        for portName in self.camPorts:
            camObj = CameraObject(portName)
            camObjs = camObjs + [camObj]
        self.camObjects = camObjs
        return self.camObjects

    def disconnectAll(self):
        for camObj in self.camObjects:
            camObj.disconnect()
            
    def startRecordingAll(self):
        startTimeObjs = []
        for camNum, camObj in enumerate(self.camObjects):
            try:
                startTimeObj = camObj.startRecording()
                startTimeObjs = startTimeObjs + [startTimeObj]
                time.sleep(0.01)
            except OpenMVError:
                self.camObjects[camNum] = camObj.reset()
        
        return startTimeObjs

    def stopRecordingAll(self):
        actualStartTimeObjs = []
        endTimeObjs = []
        actualDurations = []
        for camNum, camObj in enumerate(self.camObjects):
            try:
                actualStartTimeObj, endTimeObj, actualDuration = camObj.stopRecording()
                actualStartTimeObjs = actualStartTimeObjs + [actualStartTimeObj]
                endTimeObjs = endTimeObjs + [endTimeObj]
                actualDurations = actualDurations + [actualDuration]
        
            except Exception as e:
                print('Camera failure:\n%s' %e)
                self.camObjects[camNum] = camObj.reset()
            time.sleep(0.01)
        return actualStartTimeObjs, endTimeObjs, actualDurations
