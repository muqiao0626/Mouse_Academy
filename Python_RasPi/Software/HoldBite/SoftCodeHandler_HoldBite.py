
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
import time

class SoftCodeHandler(object):
    def __init__(self):
        self.SoftCode = True
        self.biteTime = time.time()
        self.releaseTime = time.time()

    def handleSoftCode(self, byte):
        if byte==1:
            self.biteTime = time.time()
            print("Bit!")
        elif byte==2:
            releaseTime = time.time() - self.biteTime
            print("Released after %02d ms" %int(1000*releaseTime))
        elif byte==3:
            releaseTime = time.time() - self.biteTime
            print("Released after %02d ms (early)" %int(1000*releaseTime))
        elif byte==4:
            releaseTime = time.time() - self.biteTime
            print("Bite bar stuck" )
