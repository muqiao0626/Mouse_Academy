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
import numpy as np
import time
import json
import re
import serial
import AcademyUtils
import MegaCom
from ReportCardClass import ReportCard

def main():
    megaPort = AcademyUtils.findMegaPort()
    megaSer = serial.Serial(megaPort, 9600, timeout=1)
    setupMsg = megaSer.readline().decode().strip()
    #print(setupMsg)
    time.sleep(0.5)
    readyMsg = megaSer.readline().decode().strip()
    #print(readyMsg)
    
    #only allow numbers in input
    numNewStudentsInp = input('How many students would you like to enroll? (up to 5) ')
    if not numNewStudentsInp.isdigit():
        numNewStudentsInp = input('Please enter an integer value.\nHow many students would you like to enroll? ')
        if not numNewStudentsInp.isdigit():
            print('Number of new students must be an integer value. Exiting script.')
            megaSer.close()
            return False
    #only allow number <= 5
    numNewStudents = int(numNewStudentsInp)
    if numNewStudents > 5:
        print('Number of new students must be no greater than 5. Exiting script.')
        megaSer.close()
        return False
        
    print('Use Reader 1 to scan new tags.')
    
    student = 1
    maxTime = 2*60
    while student <= numNewStudents:
        print('Scanning student %d...' %student)
        
        startTime = time.time()
        elapsed_time = 0
        while elapsed_time < maxTime:#quit program if no tags read after 2 min
            tag = MegaCom.readTag(megaSer, 1)
            time.sleep(0.5)
            if MegaCom.isTag(tag):
                rosterPath = AcademyUtils.getRosterPath()
                with open(rosterPath, 'r') as f:
                    jsonstr = f.read()
                    roster = json.loads(jsonstr)
                    
                if tag in roster['id']:
                    subject = print('Oops! "%s" is already enrolled. Moving to next student...' %tag)
                else:
                    subject = input('Enter subject name for tag %s: ' %tag)
                    label = input('Enter label for subject "%s" (optional) ' %subject)
                    roster['id'].update({tag:{'mouseID':subject, 'label':label}})
                    with open(rosterPath, 'w') as f:
                        f.write(json.dumps(roster, sort_keys=True, indent=2, separators=(',', ': '), default=AcademyUtils.json_serial))
                student += 1
                break #exit while loop if tag scanned correctly
            elapsed_time = time.time() - startTime
        #if while loop ended because reached maxTime, exit, otherwise, wait for next tag
        if elapsed_time >= maxTime:
            print('No tag detected. Exiting script.')
            megaSer.close()
            return False
            
    print('Enrollment complete! Roster saved to:\n%s' % rosterPath)
    megaSer.close()
    return True
    
if __name__ == '__main__':
    main()