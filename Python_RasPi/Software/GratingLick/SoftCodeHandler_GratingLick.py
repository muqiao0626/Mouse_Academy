
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
from pygame.locals import *
import importlib

class SoftCodeHandler(object):
    def __init__(self):
        self.gratingFlip = 0
        self.greyFlip = 0
        self.pg = importlib.import_module('pygame')
        self.pg.init()
        self.screenWidth = 1920
        self.screenHeight = 1080
        self.screen = self.pg.display.set_mode((self.screenWidth, self.screenHeight), self.pg.NOFRAME)
        self.background = self.pg.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((128, 128, 128))
        self.screen.blit(self.background,(0,0))
        self.pg.display.flip()
        
        
        self.gratingRect = self.pg.Rect((0,0),(self.screenWidth, self.screenHeight))
        self.gratingIm = self.pg.image.load("/home/pi/Mouse_Academy/Python_RasPi/Software/GratingLick/gratingIms/grating_rot=-30degrees_period=05_size=15_xoffset=+000_yoffset=+000.jpg")
        self.gratingIm = self.pg.transform.scale(self.gratingIm, self.gratingRect.size)
        self.gratingIm = self.gratingIm.convert()
        
        self.drawGrating()

        
    def drawGrey(self):
        self.screen.blit(self.background,(0,0))
    def drawGrating(self):
        self.screen.blit(self.gratingIm, self.gratingRect)

    def handleSoftCode(self, byte):

        if byte==1: #to show grating after hold
            self.pg.display.flip()
            self.gratingFlip = time.time()
            self.drawGrey()

        elif byte==2: #to show grey after lick
            self.pg.display.flip()
            self.greyFlip = time.time()
            self.drawGrating()
        elif byte==3: #to show grey after false start
            self.drawGrey()
            self.pg.display.flip()
            self.greyFlip = time.time()
            self.drawGrating()
            
        
    def close(self):
        self.pg.display.quit()
        self.pg.quit()
