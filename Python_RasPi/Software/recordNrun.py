import OpenMVCom
import AcademyUtils
import BpodClass
import importlib
from ReportCardClass import ReportCard
import time

subject = 'M01'
rc = ReportCard(subject)
bpodPort = AcademyUtils.findBpodUSBPort()

camSers, connected = OpenMVCom.connectAll()
compTimeObjs = OpenMVCom.startRecordingAll(camSers)

protocol = rc.currentProtocol
protocolModule = importlib.import_module('%s.%s' %(protocol,protocol))
print('%s beginning protocol "%s"' %(subject, protocol))
try:
    myBpod, rc = protocolModule.runProtocol(bpodPort, rc)
except Exception as e:
    print("Bpod exception:\n%s" %e)
    AcademyUtils.resetBpodPort()

actualStartTimeObjs, endTimeObjs, durs = OpenMVCom.stopRecordingAll(camSers)
OpenMVCom.disconnectAll(camSers)