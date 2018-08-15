# Mouse Academy

## Overview

Mouse Academy is an integrated platform for automated mice training. It is made of a social home cage, a radio frequency identification (RFID) access control tunnel and a training box. Mice are grouped together in the home cage where they can get free access to food and shelter. Water is provided only in the training box. Each mouse is implanted with a specific RFID chip whose information can be read from the RFID sensors. Based on the information from the RFID sensors, an Arduino circuit controls the opening of the gates, allowing only one animal at a time to access the training box. Once a mouse enters the training box, a protocol is initiated to train the mouse on a
specific task using water rewards, and a video recording of the mouse’s behaviors is performed. The training box is controlled by Bpod, an open-source behavior control system (https://github.com/sanworks/Bpod).

## Content

## 1. Firmware: Arduino program for RFID access control

### Documentation

The code was written in Arduino language (C) which has been tested on ARDUINO (IDE) 1.8.5. To run the code, you need to install the following packages:
```
Servo.h
```

### Instruction in compiling and uploading the code

Compile the code in ARDUINO (IDE) 1.8.5 and upload it to Arduino Mega 2560


## 2. Software

### Documentation

The code was written in Matlab and has been tested under Matlab R2016a. To run the code, copy all the files under /Software/Matlab_PC/ into the MATLAB folder. Modify the ProtocolFiles.xlsx to include all the training procedures. The format of the excel file is: Procedure_name, Threshold_for_downgrade, Threshold_for_upgrade, Trials_in_a_session.

### Instruction in running the code

First, run Initialization.m to initialize the program. Then, run Master.m. The program runs in an infinite loop. To exit running, pause the program and then stop the Master.m program.

## 3. Design files

The folder contains several CAD files for the hardware

## Licence

These files are freely available under the terms of General Public License v3.0 (enclosed with this repository)

## Contact

For more questions, please contact Mu Qiao at muqiao@caltech.edu
