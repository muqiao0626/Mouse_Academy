
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

import sys
import time
import oct2py

class SoftCodeHandler(object):
    def __init__(self):
        self.SoftCode = True
        self.oc = oct2py.Oct2Py()
        self.oc.chdir('/home/pi/Mouse_Academy/Python_RasPi/Software/GratingLick')
        self.grey = None
        self.window = None
        self.windowRect = None
        self.gratingFlip = 0.0
        self.greyFlip = 0.0
        
    def initialize(self):
        initStruct = self.oc.InitializeWindow()
        self.grey = initStruct.Grey
        self.window = initStruct.Window
        self.windowRect = initStruct.WindowRect
        
    def drawGrating(self):
        gaborStruct = self.oc.DrawGabor(self.window, self.windowRect)
        self.window = gaborStruct.Window
        self.windowRect = gaborStruct.WindowRect
        
    def flipScreen(self):
        flipTime = self.oc.FlipScreen(self.window)
        return flipTime
        
    def drawGrey(self):
        self.window = self.oc.DrawGrey(self.window, self.grey, self.windowRect)
        
    def close(self):
        self.oc.CloseScreen()

    def handleSoftCode(self, byte):
        print("SoftCode Byte: %d" % byte)
        
        if byte==1:
            self.gratingFlip = self.flipScreen()
            self.drawGrey()
            
        elif byte==2:
            self.greyFlip = self.flipScreen()
            self.drawGrating()
