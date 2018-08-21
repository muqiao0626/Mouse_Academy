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

import sys, os
import json
import datetime as dt
import BpodClass
import BpodUtils

class ReportCard():
    def __init__(self, subjectName):
        self.tagID = ''
        self.mouseID = subjectName
        self.reportCardFolder = BpodUtils.getReportCardDir()
        self.reportCardFile = os.path.join(self.reportCardFolder, '%s.json' % self.mouseID)
        self.startDate = 0
        self.startWeight = 0
        self.maxWater = 1 #maximum water in one day
        self.currentProtocol = ''
        self.timeIn = 0
        self.timeOut = 0
        self.waterByDay = {} #water drank in ul
        self.waterReport = {} #water drank in ul
        self.currentWeight = 0 #current weight in grams
        self.performance = {}
        self.trainingAllowed = True
        self.report = {'tagID': self.tagID,
                       'mouseID': self.mouseID,
                       'startDate': self.startDate,
                       'startWeight': self.startWeight,
                       'maxWater': self.maxWater,
                       'currentProtocol': self.currentProtocol,
                       'timeIn': self.timeIn,
                       'timeOut': self.timeOut,
                       'waterByDay': self.waterByDay,
                       'waterReport': self.waterReport,
                       'trainingAllowed': self.trainingAllowed,
                       'currentWeight': self.currentWeight,
                       'performance': self.performance}
        self.load()
            
    def load(self):
        if not os.path.isfile(self.reportCardFile):
            self.save()
        else:
            with open(self.reportCardFile, 'r') as f:
                readstr = f.read()
                loaded = json.loads(readstr)
            self.tagID = loaded['tagID']
            self.startDate = loaded['startDate']
            self.startWeight = loaded['startWeight']
            self.maxWater = loaded['maxWater']
            self.currentProtocol = loaded['currentProtocol']
            self.timeIn = loaded['timeIn']
            self.timeOut = loaded['timeOut']
            self.waterByDay = loaded['waterByDay']
            self.waterReport = loaded['waterReport']
            self.currentWeight = loaded['currentWeight']
            self.performance = loaded['performance']
            self.trainingAllowed = loaded['trainingAllowed']
            self.report = {'tagID': self.tagID,
                           'mouseID': self.mouseID,
                           'startDate': self.startDate,
                           'startWeight': self.startWeight,
                           'maxWater': self.maxWater,
                           'currentProtocol': self.currentProtocol,
                           'timeIn': self.timeIn,
                           'timeOut': self.timeOut,
                           'waterByDay': self.waterByDay,
                           'waterReport': self.waterReport,
                           'trainingAllowed': self.trainingAllowed,
                           'currentWeight': self.currentWeight,
                           'performance': self.performance}
    def getWaterToday(self):
        today = dt.date.today().isoformat()
        if today in list(self.waterByDay.keys()):
            return self.waterByDay[today]
        else:
            self.waterByDay.update({today:0})
            return 0
    def setCurrentProtocol(self, protocol):
        self.currentProtocol = protocol
        
    def setMaxWater(self, amount):
        self.maxWater = amount
        
    def getDates(self):
        days = list(self.waterByDay.keys())
        return days
                
        
    def drankWater(self, amount, sessionName):
        days = self.getDates()
        today = dt.date.today().isoformat()
        print(today, days)
        if today not in days:
            self.waterByDay.update({today:0})
        oldAmount = self.waterByDay[today]
        self.waterByDay.update({today: oldAmount + amount})
        self.waterReport.update({sessionName: amount})
        if oldAmount + amount >= self.maxWater:
            self.trainingAllowed = False
        
    def setPerformance(self, protocol, day, session, performance):
        if protocol not in self.performance.keys():
            self.performance.update({protocol:{}})
        if day not in self.performance[protocol].keys():
            self.performance[protocol].update({day:{}})
        self.performance[protocol][day].update({session:performance})
        
    def getWaterReport(self):
        return self.waterReport
    
    def save(self):
        self.report.update({'currentProtocol':self.currentProtocol,
                            'timeIn': self.timeIn,
                            'timeOut': self.timeOut,
                            'waterByDay': self.waterByDay,
                            'waterReport': self.waterReport,
                            'performance': self.performance,
                            'maxWater': self.maxWater,
                            'currentWeight': self.currentWeight,
                            'trainingAllowed': self.trainingAllowed
                            })
        with open(self.reportCardFile, 'w') as f:
            jsonStr = json.dumps(self.report, sort_keys=True, indent=4, separators=(',', ': '), default=BpodUtils.json_serial)
            f.write(jsonStr)
