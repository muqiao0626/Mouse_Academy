
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

class SoftCodeHandler(object):
    def __init__(self):
        self.SoftCode = True
        
    def initialize():
        from psychopy import visual, core  # import some libraries from PsychoPy

        #create a window
        mywin = visual.Window([800,600], monitor="testMonitor", units="deg")

        #create some stimuli
        grating000 = visual.GratingStim(win=mywin, mask="circle", size=3, pos=[0,0], sf=3)
        grating090 = visual.GratingStim(win=mywin, mask="circle", size=3, pos=[0,0], sf=3)
        grating045 = visual.GratingStim(win=mywin, mask="circle", size=3, pos=[0,0], sf=3)
        grating135 = visual.GratingStim(win=mywin, mask="circle", size=3, pos=[0,0], sf=3)

    def handleSoftCode(self, byte):
        print("SoftCode Byte: %d" % byte)
        

        #draw the stimuli and update the window
        grating.draw()
        mywin.update()

        #pause, so you get a chance to see it!
        core.wait(5.0)
