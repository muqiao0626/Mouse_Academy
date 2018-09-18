import sys
from psychopy import visual, core  # import some libraries from PsychoPy
import time
def mainTest():


    #create a window
    mywin = visual.Window([1920, 1080], monitor="hp22cwa", units="deg")

    #create some stimuli
    grating = visual.GratingStim(win=mywin, mask="circle", size=20, pos=[0,0], sf=0.2)

    #draw the stimuli and update the window
    grating.draw()
    drawtime = time.time()
    mywin.update()
    updatetime = time.time()

    #pause, so you get a chance to see it!
    core.wait(5.0)
    
    return drawtime, updatetime