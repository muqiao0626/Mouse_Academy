
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
        self.patchFlip = []
        self.blackFlip = []
        self.pg = importlib.import_module('pygame')
        self.pg.init()
        self.screenWidth = 1920
        self.screenHeight = 1080
        self.screen = self.pg.display.set_mode((self.screenWidth, self.screenHeight), self.pg.NOFRAME)
        self.background = self.pg.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((0, 0, 0))
        self.screen.blit(self.background,(0,0))
        self.pg.display.flip()
        
        
        self.patchRect = self.pg.Rect((0,0),(self.screenWidth, self.screenHeight))
        self.patchIm = self.pg.image.load("/home/pi/Mouse_Academy/Python_RasPi/Software/PatchLick/patch_size=25_xoffset=+000_yoffset=+000.jpg")
        self.patchIm = self.pg.transform.scale(self.patchIm, self.patchRect.size)
        self.patchIm = self.patchIm.convert()
        
        self.drawPatch()

        
    def drawBlack(self):
        self.screen.blit(self.background,(0,0))
        
    def drawPatch(self):
        self.screen.blit(self.patchIm, self.patchRect)
        
    def clearFlipTimes(self):
        self.patchFlip = []
        self.blackFlip = []

    def handleSoftCode(self, byte):

        if byte==1: #to show patch after hold
            startTime = time.time()
            self.drawPatch()
            self.pg.display.flip()
            completeTime = time.time()
            self.patchFlip = self.patchFlip + [completeTime]
            print('Delay:', completeTime - startTime)
        elif byte==2: #to show black after lick
            startTime = time.time()
            self.drawBlack()
            self.pg.display.flip()
            completeTime = time.time()
            self.blackFlip = self.blackFlip + [completeTime]
            print('Delay:', completeTime - startTime)
            
        
    def close(self):
        self.pg.display.quit()
        self.pg.quit()
