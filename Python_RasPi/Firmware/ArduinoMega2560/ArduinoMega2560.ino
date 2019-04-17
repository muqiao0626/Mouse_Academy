#include <Servo.h>
#include <stdio.h>

const int servoPin1 = 8;
const int servoPin2 = 9;

const int FSR_PIN1 = A0; // Pin connected to FSR/resistor divider
const int FSR_PIN2 = A1; // Pin connected to FSR/resistor divider
const float VCC = 5; // Measured voltage of Ardunio 5V line
const float R_DIV = 3300.0; // Measured resistance of 3.3k resistor

const int closeWrite = 15;
const int openWrite = 60;
const int tag1InRangePin = 52;
const int lightsPin = 50;

const char readCompleteMsg[18] = "read tag complete";
const char openMsg[19] = "open door complete";
const char closeMsg[20] = "close door complete";
const char obstructMsg[24] = "obstruction encountered";
const char trueMsg[5] = "True";
const char falseMsg[6] = "False";
const char lightsOnMsg[10] = "Lights ON";
const char lightsOffMsg[11] = "Lights OFF";
int idLen = 12;

char currentTag[13] = "000000000000";

Servo servo1;
Servo servo2;

int RFIDResetPin1 = 11;
int RFIDResetPin2 = 12;
int RFIDResetPin3 = 13;

boolean tir1 = false;
char tag1[13];
char tag2[13];
char tag3[13];
float fsrForce;

char blankTag[13] = "000000000000";

void clearCurrentTag() {
  for (int i = 0; i < 13; i++) {
    currentTag[i] = blankTag[i];
  }
}
void setTag1(char newTag[13]) {
  for (int i = 0; i < 13; i++) {
    tag1[i] = newTag[i];
  }
}
void setTag2(char newTag[13]) {
  for (int i = 0; i < 13; i++) {
    tag2[i] = newTag[i];
  }
}
void setTag3(char newTag[13]) {
  for (int i = 0; i < 13; i++) {
    tag3[i] = newTag[i];
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println("Mega is setting up...");
  Serial1.begin(9600);
  Serial2.begin(9600);
  Serial3.begin(9600);
  setTag1(blankTag);
  setTag2(blankTag);
  setTag3(blankTag);
  pinMode(tag1InRangePin, INPUT);
  pinMode(lightsPin, OUTPUT);
  //reset RFID readers
  pinMode(RFIDResetPin1, INPUT);
  //digitalWrite(RFIDResetPin1, HIGH);
  pinMode(RFIDResetPin2, INPUT);
  //digitalWrite(RFIDResetPin2, HIGH);
  pinMode(RFIDResetPin3, INPUT);
  //digitalWrite(RFIDResetPin3, HIGH);

  pinMode(FSR_PIN1, INPUT);
  pinMode(FSR_PIN2, INPUT);

  servo1.attach(servoPin1, 570, 2300);
  delay(50);
  //openDoor(servo1, 1);
  //delay(50);
  servo2.attach(servoPin2, 576, 2300);
  delay(50);
  //closeDoor(servo2, 2);
  //delay(50);
  Serial.println("Mega is ready.");

}

void loop() {
  readTag(1);
  readTag(2);
  readTag(3);

  if (Serial.available() >= 2) {
    char commandRead = Serial.read();
    char idRead = Serial.read();

    //CHECKING FOR READ COMMAND
    if (commandRead == '8') {

      Serial.println(readCompleteMsg);
      if (idRead == '1') {
        Serial.println(tag1);
        setTag1(blankTag);
      }
      else if (idRead == '2') {
        Serial.println(tag2);
        setTag2(blankTag);
      }
      else if (idRead == '3') {
        Serial.println(tag3);
        setTag3(blankTag);
      }

    }

    //CHECKING FOR OPEN DOOR COMMAND
    else if (commandRead == '6') {
      if (idRead == '1') {
        openDoor(servo1);
      }
      else if (idRead == '2') {
        openDoor(servo2);
      }
      Serial.println(openMsg);
    }

    //CHECKING FOR CLOSE DOOR COMMAND
    else if (commandRead == '7') {
      int closed = 0;
      if (idRead == '1') {
        closed = closeDoor(servo1, 1);
        if (closed == 1) {
          Serial.println(closeMsg);
        }
      }
      else if (idRead == '2') {
        closed = closeDoor(servo2, 2);
        if (closed == 1) {
          Serial.println(closeMsg);
        }
      }
    }
    //CHECK IF ANIMAL IN RANGE OF ANT1
    else if (commandRead == '9') {
      if (idRead == '0') {
      
        tag1InRange();
        if (tir1 == true){
        Serial.println(trueMsg);
        }
        else{
          Serial.println(falseMsg);
        }
    }

  }
  //TURN ON LIGHTS
    else if (commandRead == '5') {
      if (idRead == '1') {
        lightsOn(lightsPin);
      Serial.println(lightsOnMsg);
      }
        else if (idRead == '2'){
          lightsOff(lightsPin);
          Serial.println(lightsOffMsg);
        }
    }

  }
  delay(10);
}



void lightsOn(int pinNum){
  digitalWrite(pinNum, HIGH);
  
}

void lightsOff(int pinNum){
  digitalWrite(pinNum, LOW);
}

void tag1InRange(){
  tir1 = (digitalRead(tag1InRangePin) == LOW);
}


// READ A TAG FROM A SINGLE RFID READER
void readTag(int tagNum) {
  clearCurrentTag();
  HardwareSerial* serPointer;
   int address;

  if (tagNum == 1){
    serPointer = &Serial1;
  }
  else if (tagNum == 2){
    serPointer = &Serial2;
  }
  else if (tagNum == 3){
    serPointer = &Serial3;
  }
  boolean reading = false;
  int i = 0;
  int readByte;
  char peekByte;
  if (serPointer->available() >= 10) {
    peekByte = serPointer->peek(); //peep next available byte
    if (peekByte == 2) {
      readByte = serPointer->read();
      reading = true; //begining of tag

      while (reading == true) {
        readByte = serPointer->read();
        if (readByte == 3) {
          if (tagNum == 1) {
            setTag1(currentTag);
          }
          else if (tagNum == 2) {
            setTag2(currentTag);
          }
          else if (tagNum == 3) {
            setTag3(currentTag);
          }
          reading = false; //end of tag
        }

        else if (readByte != 10 && readByte != 13) {
          //store the tag
          if (i < sizeof(currentTag)) {
            currentTag[i] = readByte;
          }
          i++;
        }
        delay(2);
      }
    }
    else {
      reading = false;
      
    }
  }
  
}

int closeDoor(Servo servo, int servonum) {
  int pos = servo.read();
  int closed = 0;
  currentForce(servonum);
  float forceInit = fsrForce;
  float forceNow;
  //don't bother checking force at beginning and end
  //closeWrite is smaller angle
  for (int theta = pos; theta > closeWrite + 6; theta -= 6) {

    if (theta < openWrite + 6 || theta > closeWrite - 6) {
      servo.write(theta);
      delay(5);
      closed = 1;
    }



    else {
      servo.write(theta);
      delay(5);
//      currentForce(servonum);
//      forceNow = fsrForce - forceInit;
//      if (forceNow > 10.0) {
//        //reopen door
//        servo.write(openWrite);
//        //print serial message that close door failed
//        Serial.println(obstructMsg);
//        //Serial.print(forceInit);
//       // Serial.print(" forceNow: ");
//        //Serial.println(forceNow);
//        return 0;
//      }
    }
  }
  //Serial.print("initForce ");
  //Serial.println(forceInit);
  return 1;
}

void openDoor(Servo servo) {
  int pos = servo.read();
  for (int theta = pos; theta < openWrite - 3; theta += 3) {
    servo.write(theta);
    delay(15);
  }
}


void currentForce(int doornum)
{
  int fsrADC;
  if (doornum == 1) {
    fsrADC = analogRead(FSR_PIN1);
  }
  else if (doornum == 2) {

    fsrADC = analogRead(FSR_PIN2);
  }
  // If the FSR has no pressure, the resistance will be
  // near infinite. So the voltage should be near 0.
  if (fsrADC != 0) // If the analog reading is non-zero
  {
    // Use ADC reading to calculate voltage:
    float fsrV = fsrADC * VCC / 1023.0;
    // Use voltage and static resistor value to
    // calculate FSR resistance:
    float fsrR = R_DIV * (VCC / fsrV - 1.0);
    float fsrG = 1.0 / fsrR;
    // Serial.println("Resistance: " + String(fsrR) + " ohms");
    // Guesstimate force based on slopes in figure 3 of
    // FSR datasheet:
    // Break parabolic curve down into two linear slopes:
    if (fsrR <= 600)
      fsrForce = (fsrG - 0.00075) / 0.00000032639;
    else
      fsrForce =  fsrG / 0.000000642857;

  }
  else{
    fsrForce = 0;
  }
}
