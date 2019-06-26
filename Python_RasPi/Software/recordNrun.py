from OpenMVClass import OpenMVObject
import AcademyUtils
import BpodClass
import importlib
from MegaClass import MegaObject
from BpodClass import BpodError
from MegaClass import ReadError
from ReportCardClass import ReportCard
import time

subject = 'M01'
rc = ReportCard(subject)
devices = AcademyUtils.getDevices()
bpodPort = AcademyUtils.findBpodUSBPort(devices)
megaPort = AcademyUtils.findMegaPort(devices)
unoPort = AcademyUtils.findUnoPort(devices)
devices.update({'Arduino Mega':megaPort})
megaObj = MegaObject(megaPort, unoPort)
OpenMVCom = OpenMVObject()
OpenMVCom.startRecordingAll()

protocol = rc.currentProtocol
protocolModule = importlib.import_module('%s.%s' %(protocol,protocol))
print('%s beginning protocol "%s"' %(subject, protocol))
try:
    myBpod, rc, megaObj = protocolModule.runProtocol(bpodPort, rc, megaObj)
except Exception as e:
    print("Bpod exception:\n%s" %e)
    bpodPort = AcademyUtils.resetBpodPort(bpodUSBPort=bpodPort)
    '''
except ReadError as e:
    print("Mega exception:\n%s" %e)
    megaObj.disconnect()
    '''

actualStartTimeObjs, endTimeObjs, durs = OpenMVCom.stopRecordingAll()
OpenMVCom.disconnectAll()