'''
10/19/19
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

import sensor, image, time, mjpeg, pyb, os, uos, machine
import ustruct as struct
##############################
# Initialize camera and connection
# (only runs once upon establishing
# serial connection)
sensor.reset() # Initialize the camera sensor.
RED_LED_PIN = 1
BLUE_LED_PIN = 3
sensor.set_pixformat(sensor.GRAYSCALE) # or sensor.GRAYSCALE
sensor.set_framesize(sensor.VGA) # or sensor.QQVGA (or others)
sensor.set_windowing((320, 0, 160, 120))

sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
# Need to let the above settings get in...
sensor.skip_frames(time = 500)
current_exposure_time_in_microseconds = sensor.get_exposure_us()
sensor.set_auto_exposure(False, \
    exposure_us = 1000)

sensor.skip_frames(time = 2000) # Let new settings take affect.

# create a new USB_VCP object
usb_vcp = pyb.USB_VCP()
usb_vcp.setinterrupt(-1)
connected = usb_vcp.isconnected()
if connected:
    pyb.LED(BLUE_LED_PIN).on()
    pyb.delay(500)
    pyb.LED(BLUE_LED_PIN).off()
#print(connected)
#usb_vcp.send(int(connected))
nBytes = 13
compTimeRead = False
compTimeBuff = bytearray(nBytes)
clock = time.clock() # Tracks FPS.
# end of initialization code
##############################

while(True):
    ###########################
    # Check serial buffer until
    # a unix time is read.
    # READ unix time from computer
    ###############################

    while not compTimeRead:
        # returns number of bytes read
        compTimeBuff = usb_vcp.recv(nBytes, timeout=0)
        bytesRead = len(compTimeBuff)
        if bytesRead >3: #nBytes:
            compTimeRead = True
            pyb.LED(RED_LED_PIN).on()
            readTime = pyb.millis()
        pyb.delay(10)

    while compTimeRead:
        ######################################
        # Time has been read. Parse to string
        # to name movie folder.

        compTimeFmt = "<" + str(nBytes) + "s"
        compTimePack = struct.unpack(compTimeFmt, compTimeBuff)
        compTimeStr = compTimePack[0].decode()
        compTime = int(compTimeStr)

        # Turn on red LED to indicate frame capture.
        #pyb.LED(RED_LED_PIN).on()

        uos.mkdir(compTimeStr)
        pyb.delay(100)
        fname = compTimeStr + '/' + compTimeStr + '.txt'
        #fname = ''.join([compTimeStr, '-', compTimeStr, '.txt'])
        f = open(fname, 'a+')
        endRead = False
        endReadBuff = bytearray(4)
        recordTime = pyb.millis()
        i = 0

        # Find time elapsed since start signal was read.
        recordLatency = pyb.elapsed_millis(readTime)
        while not endRead:
            #capture 5 frames before checking for end signal
            for x in range(5):
                frameStart = pyb.elapsed_millis(recordTime)
                img = sensor.snapshot().compress()
                imgPath = compTimeStr + '/' + '%06d.jpg' % i
                img.save(imgPath)
                i += 1
                f.write(str(frameStart + recordLatency))
                f.write('\r\n')
                pyb.delay(15)
            endBytesRead = usb_vcp.recv(endReadBuff, timeout=0)
            if endReadBuff==b'stop':
                endRead = True
        pyb.LED(RED_LED_PIN).off()

        vidStart = int(recordLatency*0.001) + compTime
        vidEnd = int(frameStart*0.001) + vidStart

        f.close()
        vidStartStr ='{:013d}'.format(int(vidStart))
        vidEndStr = '{:013d}'.format(int(vidEnd))
        startEndEncoded = ', '.join([vidStartStr, vidEndStr]).encode()
        usb_vcp.send(bytearray(startEndEncoded))
        stats = open(''.join([compTimeStr, '/movie_info.txt']), 'w')
        stats.write("start\t")
        stats.write(vidStartStr)
        stats.write("\r\nend\t")
        stats.write(vidEndStr)
        stats.close()
        compTimeRead = False
