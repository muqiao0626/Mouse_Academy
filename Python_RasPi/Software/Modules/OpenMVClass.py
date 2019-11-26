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
        self.camObjects = {}
        if connectAll:
            self.camObjects = self.connectAll()
        self.portNames = portNames
        
    def findNewPortNames(self):
        self.portNames = AcademyUtils.getCamPorts()
        camObjPorts = []
        for pn in self.camObjects:
            camObj = self.camObjects[pn]
            if not camObj.portName is None:
                camObjPorts = camObjPorts + [camObj.portName]
        newPortNames = list(set(self.portNames) - set(camObjPorts))
        return newPortNames
        
    def connectAll(self):
        camObjs = {}
        for portName in self.camPorts:
            camObj = CameraObject(portName)
            camObjs.update({portName: camObj})
        self.camObjects = camObjs
        return self.camObjects

    def disconnectAll(self):
        for camObj in self.camObjects:
            camObj.disconnect()
            
    def startRecordingAll(self):
        startTimeObjs = []
        for pn in self.camObjects:
            camObj = self.camObjects[pn]
            try:
                startTimeObj = camObj.startRecording()
                startTimeObjs = startTimeObjs + [startTimeObj]
                time.sleep(0.01)
            except OpenMVError:
                print('Camera disconnected. Restarting...')
                newPortNames = self.findNewPortNames()
                del self.camObjects[pn]
                camObj.portName = newPortNames[0]
                camObj.connect()
                self.camObjects.update({camObj.portName: camObj})
                try:
                    startTimeObj = camObj.startRecording()
                    startTimeObjs = startTimeObjs + [startTimeObj]
                    time.sleep(0.01)
                except:
                    print('Unable to establish connection with camera.')
                #self.camObjects[camNum] = camObj.reset()
        
        return startTimeObjs

    def stopRecordingAll(self):
        actualStartTimeObjs = []
        endTimeObjs = []
        actualDurations = []
        for pn in self.camObjects:
            camObj = self.camObjects[pn]
            if camObj.isRecording:
                try:
                    actualStartTimeObj, endTimeObj, actualDuration = camObj.stopRecording()
                    actualStartTimeObjs = actualStartTimeObjs + [actualStartTimeObj]
                    endTimeObjs = endTimeObjs + [endTimeObj]
                    actualDurations = actualDurations + [actualDuration]
        
                except OpenMVError as e:
                    print('Camera failure:\n%s' %e)
                    newPortNames = self.findNewPortNames()
                    del self.camObjects[pn]
                    camObj.portName = newPortNames[0]
                    camObj.connect()
                    self.camObjects.update({camObj.portName: camObj})
            time.sleep(0.01)
        return actualStartTimeObjs, endTimeObjs, actualDurations
