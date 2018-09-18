# Mouse Academy

## Overview

Mouse Academy is an integrated platform for automated mice training. It is made of a social home cage, a radio frequency identification (RFID) access control tunnel and a training box. Mice are grouped together in the home cage where they can get free access to food and shelter. Water is provided only in the training box. Each mouse is implanted with a specific RFID chip whose information can be read from the RFID sensors. Based on the information from the RFID sensors, an Arduino circuit controls the opening of the gates, allowing only one animal at a time to access the training box. Once a mouse enters the training box, a protocol is initiated to train the mouse on a specific task using water rewards, and a video recording of the mouse’s behaviors is performed. The training box is controlled by Bpod, an open-source behavior control system (https://github.com/sanworks/Bpod).

## Content

## 1. Design files

The folder contains several CAD files for the hardware

## 2. Firmware and software

The folders MATLAB_PC and Python_RasPi contain the firmware and software designed for the specific system. In both folders, you can find:

### Firmware: Arduino program for RFID access control

#### Documentation

The code was written in Arduino language (C) which has been tested on ARDUINO (IDE) 1.8.5. To run the code, you need to install the following packages:
```
Servo.h
```

#### Instruction in compiling and uploading the code

Compile the code in ARDUINO (IDE) 1.8.5 and upload it to Arduino Mega 2560


### Software and the instruction in running the software

Check the software folder and the corresponding txt files for instructions

## Licence

These files are freely available under the terms of General Public License v3.0 (enclosed with this repository)

## Acknowledgement

We thank Josh Sanders (Sanworks) for his advice on how to incorporate Bpod in Mouse Academy.

## Contact

For more questions, please contact Mu Qiao at muqiao@caltech.edu and Sarah Sam at ssam@caltech.edu
