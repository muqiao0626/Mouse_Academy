import oct2py
import struct
import numpy as np
import time

oc = oct2py.Oct2Py()

oc.chdir('/home/pi/Mouse_Academy/Python_RasPi/Software/GratingLick')
stru = oc.InitializeWindow()
grey = stru.Grey
window = stru.Window
windowRect = stru.WindowRect
print('grey:', grey)
print('InitializeWindow:', window)
print('windowRect:', windowRect)

gaborstru = oc.DrawGabor(window, windowRect)
window = gaborstru.Window
windowRect = gaborstru.WindowRect
print('GaborWindow:', window)

flipTime = oc.FlipScreen(window)
print('FlipTime:', flipTime)
time.sleep(1)

window = oc.DrawGrey(window, grey, windowRect)
flipTime = oc.FlipScreen(window)
time.sleep(1)

oc.CloseScreen()