
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
        self.SoftCode = True
        self.biteTime = time.time()
        self.releaseTime = time.time()
        
        self.gratingFlip = None
        self.grayFlip = None
        self.whiteFlip = None
        self.gratingAngle = None
        self.gratingPos = None
        self.pg = importlib.import_module('pygame')
        self.pg.init()
        self.screenWidth = 1440
        self.screenHeight = 900
        self.screen = self.pg.display.set_mode((self.screenWidth, self.screenHeight), self.pg.NOFRAME)
        self.grayBackground = self.pg.Surface(self.screen.get_size())
        self.grayBackground = self.grayBackground.convert()
        self.grayBackground.fill((128, 128, 128))
        self.screen.blit(self.grayBackground,(0,0))
        self.pg.display.flip()
        
        #horizontal grating
        self.screenRect = self.pg.Rect((0,0),(self.screenWidth, self.screenHeight))
        self.gratingImHorzCenter = self.pg.image.load("/home/pi/Mouse_Academy/Python_RasPi/Software/GratingBite/gratingIms/grating_rot=+90degrees_period=05_size=15_xoffset=+000_yoffset=+000_contrast=100.jpg")
        self.gratingImHorzCenter = self.pg.transform.scale(self.gratingImHorzCenter, self.screenRect.size)
        self.gratingImHorzCenter = self.gratingImHorzCenter.convert()
        
        self.screenRect = self.pg.Rect((0,0),(self.screenWidth, self.screenHeight))
        self.gratingImHorzLeft = self.pg.image.load("/home/pi/Mouse_Academy/Python_RasPi/Software/GratingBite/gratingIms/grating_rot=+90degrees_period=05_size=15_xoffset=-500_yoffset=+000_contrast=100.jpg")
        self.gratingImHorzLeft = self.pg.transform.scale(self.gratingImHorzLeft, self.screenRect.size)
        self.gratingImHorzLeft = self.gratingImHorzLeft.convert()
        
        #verticalGrating

        self.gratingImVertCenter = self.pg.image.load("/home/pi/Mouse_Academy/Python_RasPi/Software/GratingBite/gratingIms/grating_rot=+00degrees_period=05_size=15_xoffset=+000_yoffset=+000_contrast=100.jpg")
        self.gratingImVertCenter = self.pg.transform.scale(self.gratingImVertCenter, self.screenRect.size)
        self.gratingImVertCenter = self.gratingImVertCenter.convert()

        self.gratingImVertLeft = self.pg.image.load("/home/pi/Mouse_Academy/Python_RasPi/Software/GratingBite/gratingIms/grating_rot=+00degrees_period=05_size=15_xoffset=-500_yoffset=+000_contrast=100.jpg")
        self.gratingImVertLeft = self.pg.transform.scale(self.gratingImVertLeft, self.screenRect.size)
        self.gratingImVertLeft = self.gratingImVertLeft.convert()
        
        
        #white background

        
        self.whiteBackground = self.pg.Surface(self.screen.get_size())
        self.whiteBackground = self.whiteBackground.convert()
        self.whiteBackground.fill((255, 255, 255))
        
        self.imDict = {'horzCenter':self.gratingImHorzCenter,
                       'vertCenter':self.gratingImVertCenter,
                       'horzLeft':self.gratingImHorzLeft,
                       'vertLeft':self.gratingImVertLeft}
        self.drawGray()
        self.pg.display.flip()

        
    def drawGray(self):
        self.screen.blit(self.grayBackground,(0,0))
        
    def drawWhite(self):
        self.screen.blit(self.whiteBackground,(0,0))
        
    def drawGrating(self, imKey):
        self.screen.blit(self.imDict[imKey], self.screenRect)
        
    def clearFlipTimes(self):
        self.gratingFlip = []
        self.grayFlip = []

    def handleSoftCode(self, byte):
        if byte==1:
            self.biteTime = time.time()

        elif byte==2: #to show grating after bite
            self.gratingTime = time.time()
            self.drawGrating('horzCenter')
            self.pg.display.flip()
            completeTime = time.time()
            self.gratingFlip = completeTime
            self.gratingAngle = 90
            self.gratingPos = "Center"
            displayDelay = completeTime - self.biteTime
            #flipDelay = completeTime - self.gratingTime
            #print("Flip delay: %02d ms" %int(1000*flipDelay))
            print("Displayed after %02d ms" %int(1000*displayDelay))

        elif byte==3: #to show grating after bite
            self.gratingTime = time.time()
            self.drawGrating('horzLeft')
            self.pg.display.flip()
            completeTime = time.time()
            self.gratingFlip = completeTime
            self.gratingAngle = 90
            self.gratingPos = "Left"
            displayDelay = completeTime - self.biteTime
            #flipDelay = completeTime - self.gratingTime
            #print("Flip delay: %02d ms" %int(1000*flipDelay))
            print("Displayed after %02d ms" %int(1000*displayDelay))
            
        elif byte==4: #to show grating after bite
            self.gratingTime = time.time()
            self.drawGrating('vertCenter')
            self.pg.display.flip()
            completeTime = time.time()
            self.gratingFlip = completeTime
            self.gratingAngle = 0
            self.gratingPos = "Center"
            displayDelay = completeTime - self.biteTime
            #flipDelay = completeTime - self.gratingTime
            #print("Flip delay: %02d ms" %int(1000*flipDelay))
            
        elif byte==5: #to show grating after bite
            self.gratingTime = time.time()
            self.drawGrating('vertLeft')
            self.pg.display.flip()
            completeTime = time.time()
            self.gratingFlip = completeTime
            self.gratingAngle = 0
            self.gratingPos = "Left"
            displayDelay = completeTime - self.biteTime
            #flipDelay = completeTime - self.gratingTime
            #print("Flip delay: %02d ms" %int(1000*flipDelay))
            print("Displayed after %02d ms" %int(1000*displayDelay))
            
        elif byte==6: #to show gray after release
            self.releaseTime = time.time()
            self.drawGray()
            self.pg.display.flip()
            completeTime = time.time()
            self.grayFlip = completeTime
            self.biteDur = self.releaseTime - self.biteTime
            print("Released after %02d ms" %int(1000*self.biteDur))
            
        elif byte==7: #to show white after early release or miss
            self.releaseTime = time.time()
            self.drawWhite()
            self.pg.display.flip()
            completeTime = time.time()
            self.whiteFlip = completeTime
            self.biteDur = self.releaseTime - self.biteTime
            print("Released after %02d ms (no reward)" %int(1000*self.biteDur))
        elif byte==8:
            print("Bite bar stuck" )
        elif byte==9:#to show gray after miss
            self.drawGray()
            self.pg.display.flip()
            completeTime = time.time()
            self.grayFlip = completeTime
            
        
    def close(self):
        self.pg.display.quit()
        self.pg.quit()
