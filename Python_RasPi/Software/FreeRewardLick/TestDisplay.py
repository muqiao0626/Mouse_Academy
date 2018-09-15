import oct2py

oc = oct2py.Oct2Py()

oc.chdir('/home/pi/Mouse_Academy/Python_RasPi/Software/FreeRewardLick')
stru = oc.TestDisplay()
print('stru:', stru)
#screenXPixels, screenYPixels, width, height, maxLum = oc.TestDisplay()
#infoTup = (screenXPixels, screenYPixels, width, height, maxLum)
#print("screenXPixels: %d\nscreenYPixels: %d\nwidth: %d\nheight: %d\nmaxLum: %d" % infoTup)