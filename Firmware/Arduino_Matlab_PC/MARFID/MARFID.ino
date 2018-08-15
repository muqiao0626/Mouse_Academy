//// Copyright (C) 2018 Meister & Perona Lab at Caltech
//// -----------------------------------------------------
////
//// This program is free software: you can redistribute it and/or modify
//// it under the terms of the GNU General Public License as published by
//// the Free Software Foundation, either version 3 of the License, or
//// (at your option) any later version.
////
//// This program is distributed in the hope that it will be useful,
//// but WITHOUT ANY WARRANTY; without even the implied warranty of
//// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//// GNU General Public License for more details.
////
//// You should have received a copy of the GNU General Public License
//// along with this program.  If not, see <http://www.gnu.org/licenses/>.


#include <Servo.h>

int RFIDResetPin1 = 11;
int RFIDResetPin2 = 12;
int RFIDResetPin3 = 13;

//Register your RFID tags here, usually upto 5 tags are used and the last one is for testing
char tag1[13] = "00782B17ACE8";
char tag2[13] = "00782B1B6F27";
char tag3[13] = "00782B18307B";
char tag4[13] = "00782B17D591";
char tag5[13] = "00782B19CF85";
char tag6[13] = "000C044DFDB8";

Servo lockServo1;
Servo lockServo2;

const int servoPin1 = 8;
const int servoPin2 = 9;

const int tagLen = 16;
const int idLen = 13;
const int kTags = 5;
const int kReaders = 3;
const int tagBuffer = 350;

int incomingByte = 1;
int incomingByte2 = 1;
int exchange = 0;

int ErrorEmpty = -1;
int ErrorEntry = -2;
int ErrorLeaving = -3;
int ErrorNoMatching = -4;

void setup() {
  Serial.begin(9600);
  Serial1.begin(9600);
  Serial2.begin(9600);
  Serial3.begin(9600);

  pinMode(RFIDResetPin1, OUTPUT);
  digitalWrite(RFIDResetPin1, HIGH);
  pinMode(RFIDResetPin2, OUTPUT);
  digitalWrite(RFIDResetPin2, HIGH);
  pinMode(RFIDResetPin3, OUTPUT);
  digitalWrite(RFIDResetPin3, HIGH);

  //ONLY NEEDED IF CONTROLING THESE PINS - EG. LEDs
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);

  // Attaches the servo to the pin
  lockServo1.attach(servoPin1, 1000, 2000);    //can have additional parameters for min and max pulse widths
  lockServo2.attach(servoPin2, 1000, 2000);    //can have additional parameters for min and max pulse widths


  // Put servo in locked position
  lockServo1.write(20);  
  lockServo2.write(160); 
}

void loop() {
  static int flag[kReaders] = {0, 0, 0};
  static int count[kReaders] = {0, 0, 0};
  static int currentTag = 0;
  static int tempTag = 0;

  char tagString[idLen];
  static int tags1[tagBuffer];
  static int tags2[tagBuffer];
  static int tags3[tagBuffer];

  int i = 0;

  boolean reading = false;

  int t = 0;

  if (incomingByte == 1) {

    static int pass1 = 0;
    static int pass2 = 0;
    static boolean in = true;

    if (exchange == 1) {
      in = false;
    }

    while (pass1 == 0) {

      if (Serial1.available()) {

        int readByte = Serial1.read(); //read next available byte

        if (readByte == 2) {
          reading = true; //begining of tag
          lightLED(2);
        }
        if (readByte == 3) {
          reading = false; //end of tag

          if (checkTag(tagString) == 0) {
            // Serial.println(ErrorEmpty);
            // Serial.println("Empty in reader 1!");
          }
          else t = checkTag(tagString);

          if (flag[0] == 0) {
            tags1[0] = t;
            flag[0] = 1;
          }
          else {
            if (t != tags1[count[0]]) {
              count[0]++;
              tags1[count[0]] = t;
            } 
          }
          t = 0;
          i = clearTag(tagString); //Clear Tag
          resetReader(); //Reset the RFID reader
        }

        if (reading && readByte != 2 && readByte != 10 && readByte != 13) {
          //store the tag
          tagString[i] = readByte;
          i++;
        }     
      }

      
      if (Serial2.available()) {

        int readByte = Serial2.read(); //read next available byte

        if (readByte == 2) {
          reading = true; //begining of tag
          lightLED(3);
        }
        if (readByte == 3) {
          reading = false; //end of tag

          if (checkTag(tagString) == 0) {
//            Serial.println(ErrorEmpty);
//            Serial.println("Empty in reader 2!");
          }
          else t = checkTag(tagString);

          if (flag[1] == 0) {
            tags2[0] = t;
            flag[1] = 1;
          }
          else {
            if (t != tags2[count[1]]) {
              count[1]++;
              tags2[count[1]] = t;
            } 
          }
          t = 0;
          i = clearTag(tagString); //Clear Tag
          resetReader(); //Reset the RFID reader
        }

        if (reading && readByte != 2 && readByte != 10 && readByte != 13) {
          //store the tag
          tagString[i] = readByte;
          i++;
        }      
      }

      if (in == true) {
        if (flag[0] == 0 && flag[1] == 1) {
          in = false;
        }
        if (flag[0] == 1 && flag[1] == 1) {
          if (tags1[count[0]] == tags2[count[1]]) {
            lockServo1.write(160); 
            delay(1000);
            
            tempTag = tags2[count[1]];
            Serial.println(tempTag);  //Here to send this information to the computer together with time
            Serial.println("An animal wants to enter the training box!");
            incomingByte2 = 1;
            
            while (incomingByte2 == 1) {
              if (Serial.available()) {
                // read the incoming byte:
                incomingByte2 = Serial.read();
                if (incomingByte2 == '1') {
                  in = false;
                  lockServo1.write(20);
                //Restore settings
                  clearTagArray(tags3, count, 2);
                  clearTagArray(tags2, count, 1);
                  clearTagArray(tags1, count, 0);
                  flag[0] = 0; count[0] = 0;
                  flag[1] = 0; count[1] = 0;
                  flag[2] = 0; count[2] = 0;
                }
                else if (incomingByte2 == '2') {
                  lockServo2.write(20); 
                  pass1 = 1;
                }
              }
            }
          }
          else {
            in = false;
          }
        }
      }
      else {
        if (flag[0] == 1 && flag[1] == 1) {
          if (tags1[count[0]] == tags2[count[1]]) {
            clearTagArray(tags2, count, 1);
            clearTagArray(tags1, count, 0);
            in = true;
            flag[0] = 0; count[0] = 0;
            flag[1] = 0; count[1] = 0;
            exchange = 0;
          }
        }
      }     
    }

    while (pass2 == 0) {

      if (Serial3.available()) {

        int readByte = Serial3.read(); //read next available byte

        if (readByte == 2) {
          reading = true; //begining of tag
          lightLED(4);
        }

        if (readByte == 3) {
          reading = false; //end of tag

          if (checkTag(tagString) == 0) {
            // Serial.println(ErrorEmpty);
            // Serial.println("Empty in reader 3!");
          }
          else t = checkTag(tagString);

          if (flag[2] == 0) {
            tags3[0] = t;
            flag[2] = 1;
          }
          else {
            if (t != tags3[count[2]]) {
              count[2]++;
              tags3[count[2]] = t;
            } 
            count[2]++;
            tags3[count[2]] = t;
          }
          t = 0;
          i = clearTag(tagString); //Clear Tag
          resetReader(); //Reset the RFID reader
        }

        if (reading && readByte != 2 && readByte != 10 && readByte != 13) {
          //store the tag
          tagString[i] = readByte;
          i++;
        }
      }

      if (in == true) {
        if (flag[2] == 1 && flag[1] == 1) {
          if (tags3[count[2]] == tags2[count[1]]) {
            lockServo2.write(160); 
            pass2 = 1;
          }
        }
      }       
    }

    if (pass1 == 1 && pass2 == 1) {
      currentTag = tags3[count[2]];
      Serial.println(currentTag);  //Here to send this information to the computer together with time
      Serial.println("An animal enters the training box!");
      

      while (pass1 == 1 && pass2 == 1) {
        if (Serial.available()) {
          // read the incoming byte:
          incomingByte = Serial.read();
          if (incomingByte == '0') {
            clearTagArray(tags3, count, 2);
            clearTagArray(tags2, count, 1);
            clearTagArray(tags1, count, 0);
            flag[0] = 0; count[0] = 0;
            flag[1] = 0; count[1] = 0;
            flag[2] = 0; count[2] = 0;

            pass1 = 0;
            pass2 = 0;

            while (Serial2.available()) {
              int readByte = Serial2.read(); //read next available byte
            }
          }
        }
      }
    }
  }

  else {

    lockServo2.write(20);  
    
    static int pass1 = 0;
    static int pass2 = 0;
    static boolean out = true;

    while (pass2 == 0) {

      if (Serial3.available()) {

        int readByte = Serial3.read(); //read next available byte

        if (readByte == 2) {
          reading = true; //begining of tag
          lightLED(4);
        }

        if (readByte == 3) {
          reading = false; //end of tag

          if (checkTag(tagString) == 0) {
            // Serial.println(ErrorEmpty);
            // Serial.println("Empty in reader 3!");
          }
          else t = checkTag(tagString);

          if (flag[2] == 0) {
            tags3[0] = t;
            flag[2] = 1;
          }
          else {
            if (t != tags3[count[2]]) {
              count[2]++;
              tags3[count[2]] = t;
            } 
          }
          t = 0;
          i = clearTag(tagString); //Clear Tag
          resetReader(); //Reset the RFID reader
        }

        if (reading && readByte != 2 && readByte != 10 && readByte != 13) {
          //store the tag
          tagString[i] = readByte;
          i++;
        }
      }

      if (Serial2.available()) {

        int readByte = Serial2.read(); //read next available byte

        if (readByte == 2) {
          reading = true; //begining of tag
          lightLED(3);
        }
        if (readByte == 3) {
          reading = false; //end of tag

          if (checkTag(tagString) == 0) {
//            Serial.println(ErrorEmpty);
//            Serial.println("Empty in reader 2!");
          }
          else t = checkTag(tagString);

          if (flag[1] == 0) {
            tags2[0] = t;
            flag[1] = 1;
          }
          else {
            if (t != tags2[count[1]]) {
              count[1]++;
              tags2[count[1]] = t;
            } 
          }
          t = 0;
          i = clearTag(tagString); //Clear Tag
          resetReader(); //Reset the RFID reader
        }

        if (reading && readByte != 2 && readByte != 10 && readByte != 13) {
          //store the tag
          tagString[i] = readByte;
          i++;
        }
      }

      if (out == true) {
        if (flag[2] == 1 && flag[1] == 1) {
          if (tags3[count[2]] == tags2[count[1]]) {
            lockServo2.write(160);  
            delay(1000);
            lockServo1.write(20);  
            pass2 = 1;
          }
        }
      } 
    }

    while (pass1 == 0) {

      if (Serial1.available()) {

        int readByte = Serial1.read(); //read next available byte

        if (readByte == 2) {
          reading = true; //begining of tag
          lightLED(2);
        }
        if (readByte == 3) {
          reading = false; //end of tag

          if (checkTag(tagString) == 0) {
            // Serial.println(ErrorEmpty);
            // Serial.println("Empty in reader 1!");
          }
          else t = checkTag(tagString);

          if (flag[0] == 0) {
            tags1[0] = t;
            flag[0] = 1;
          }
          else {
            if (t != tags1[count[0]]) {
              count[0]++;
              tags1[count[0]] = t;
            } 
          }
          t = 0;
          i = clearTag(tagString); //Clear Tag
          resetReader(); //Reset the RFID reader
        }

        if (reading && readByte != 2 && readByte != 10 && readByte != 13) {
          //store the tag
          tagString[i] = readByte;
          i++;
        }
      }
      
      if (Serial2.available()) {

        int readByte = Serial2.read(); //read next available byte

        if (readByte == 2) {
          reading = true; //begining of tag
          lightLED(3);
        }
        if (readByte == 3) {
          reading = false; //end of tag

          if (checkTag(tagString) == 0) {
//            Serial.println(ErrorEmpty);
//            Serial.println("Empty in reader 2!");
          }
          else t = checkTag(tagString);

          if (flag[1] == 0) {
            tags2[0] = t;
            flag[1] = 1;
          }
          else {
            if (t != tags2[count[1]]) {
              count[1]++;
              tags2[count[1]] = t;
            } 
          }
          t = 0;
          i = clearTag(tagString); //Clear Tag
          resetReader(); //Reset the RFID reader
        }

        if (reading && readByte != 2 && readByte != 10 && readByte != 13) {
          //store the tag
          tagString[i] = readByte;
          i++;
        }
      }

      if (out == true) {
        if (flag[0] == 1 && flag[1] == 1) {
          if (tags1[count[0]] == currentTag) {
            pass1 = 1;
            if (tags2[count[1]] != currentTag) {
              exchange = 1;
            }
          }
        }
      } 
    }


    if (pass1 == 1 && pass2 == 1) {
      Serial.println(tags3[count[2]]);  //Here to send this information to the computer together with time
      Serial.println("An animal enters the home cage!");
      //Restore settings
      clearTagArray(tags3, count, 2);
      clearTagArray(tags2, count, 1);
      clearTagArray(tags1, count, 0);
      flag[0] = 0; count[0] = 0;
      flag[1] = 0; count[1] = 0;
      flag[2] = 0; count[2] = 0;

      incomingByte = 1;
      pass1 = 0;
      pass2 = 0;    
    }
  }
}

int checkTag(char tag[]) {
  ///////////////////////////////////
  //Check the read tag against known tags
  ///////////////////////////////////

  if (strlen(tag) == 0) return 0; //empty, no need to contunue

  if (compareTag(tag, tag1)) { // if matched tag1, do this

    return 1;

  } else if (compareTag(tag, tag2)) { 

    return 2;

  } else if (compareTag(tag, tag3)) {

    return 3;

  } else if (compareTag(tag, tag4)) {

    return 4;

  } else if (compareTag(tag, tag5)) {

    return 5;

  } else if (compareTag(tag, tag6)) {

    return 6;    

  } else {

    return -1;
  }

}

void lightLED(int pin) {
  ///////////////////////////////////
  //Turn on LED on pin "pin" for 250ms
  ///////////////////////////////////

  digitalWrite(pin, HIGH);
  delay(10);
  digitalWrite(pin, LOW);
}

void resetReader() {
  ///////////////////////////////////
  //Reset the RFID reader to read again.
  ///////////////////////////////////
  // digitalWrite(RFIDResetPin0, LOW);
  //digitalWrite(RFIDResetPin0, HIGH);
  digitalWrite(RFIDResetPin1, LOW);
  digitalWrite(RFIDResetPin1, HIGH);
  digitalWrite(RFIDResetPin2, LOW);
  digitalWrite(RFIDResetPin2, HIGH);
  digitalWrite(RFIDResetPin3, LOW);
  digitalWrite(RFIDResetPin3, HIGH);
  delay(10);
}

int clearTag(char one[]) {
  ///////////////////////////////////
  //clear the char array by filling with null - ASCII 0
  //Will think same tag has been read otherwise
  ///////////////////////////////////
  for (int i = 0; i < strlen(one); i++) {
    one[i] = 0;
  }

  return 0;
}

void clearTagArray(int array[], int count[], int a) {
  ///////////////////////////////////
  //clear the char array by filling with null - ASCII 0
  //Will think same tag has been read otherwise
  ///////////////////////////////////
  for (int j = count[a]; j >= 0; j--) {
    array[j] = 0;
  }

  count[a] = 0;
}

boolean compareTag(char one[], char two[]) {
  ///////////////////////////////////
  //compare two value to see if same,
  //strcmp not working 100% so we do this
  ///////////////////////////////////

  if (strlen(one) == 0) return false; //empty

  for (int i = 0; i < 12; i++) {

    if (one[i] != two[i]) return false;
  }

  return true; //no mismatches
}
