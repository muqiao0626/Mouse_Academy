#include <Servo.h>
#include <stdio.h>

const int servoPin1 = 8;
const int servoPin2 = 9;

const int FSR_PIN1 = A0; // Pin connected to FSR/resistor divider
const int FSR_PIN2 = A1; // Pin connected to FSR/resistor divider
const float VCC = 5; // Measured voltage of Ardunio 5V line
const float R_DIV = 3300.0; // Measured resistance of 3.3k resistor

const int highWrite = 170;
const int lowWrite = 5;
int idLen = 12;

Servo servo1;
Servo servo2;

int RFIDResetPin1 = 11;
int RFIDResetPin2 = 12;
int RFIDResetPin3 = 13;

char tag1[13];
char tag2[13];
char tag3[13];

char blankTag[13] = "000000000000";
void setTag(char oldTag[13], char newTag[13]){
  for (int i=0; i<13; i++){
    oldTag[i] = newTag[i];
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println("Mega is setting up...");
  Serial1.begin(9600);
  Serial2.begin(9600);
  Serial3.begin(9600);
  setTag(tag1, blankTag);
  setTag(tag2, blankTag);
  setTag(tag3, blankTag);
  //reset RFID readers
  pinMode(RFIDResetPin1, INPUT);
  //digitalWrite(RFIDResetPin1, HIGH);
  pinMode(RFIDResetPin2, INPUT);
  //digitalWrite(RFIDResetPin2, HIGH);
  pinMode(RFIDResetPin3, INPUT);
  //digitalWrite(RFIDResetPin3, HIGH);
  
  pinMode(FSR_PIN1, INPUT);
  pinMode(FSR_PIN2, INPUT);
  
  servo1.attach(servoPin1, 400, 1900);
  delay(50);
  //openDoor(servo1, 1);
  //delay(50);
  servo2.attach(servoPin2, 500, 2000);
  delay(50);
  //closeDoor(servo2, 2);
  //delay(50);
  Serial.println("Mega is ready.");

}

void loop() {
    readTag(Serial1, tag1);
    readTag(Serial2, tag2);
    readTag(Serial3, tag3);

  if (Serial.available() >= 2){
    char commandRead = Serial.read();
    char idRead = Serial.read();
    
    //CHECKING FOR READ COMMAND
    if (commandRead == '8'){
      
      Serial.println("read tag complete");
      if (idRead =='1'){
        Serial.println(tag1);
        setTag(tag1, blankTag);
      }
      else if (idRead =='2'){
        Serial.println(tag2);
        setTag(tag2, blankTag);
      }
      else if (idRead =='3'){
        Serial.println(tag3);
        setTag(tag3, blankTag);
      }

    }
    
    //CHECKING FOR OPEN DOOR COMMAND
    else if (commandRead == '6'){
      if (idRead == '1'){
        openDoor(servo1);
      }
      if (idRead == '2'){
        openDoor(servo2);
      }
      Serial.println("open door complete");
    }
    
    //CHECKING FOR CLOSE DOOR COMMAND
    else if (commandRead == '7'){
      int closed = 0;
      if (idRead == '1'){
        closed = closeDoor(servo1, 1);
        if (closed == 1){
          Serial.println("close door complete");
        }
      }
      if (idRead == '2'){
        closed = closeDoor(servo2, 2);
        if (closed == 1){
          Serial.println("close door complete");
        }
      }
    }

  }
  delay(50);
}







// READ A TAG FROM A SINGLE RFID READER
void readTag(HardwareSerial ser, char workingTag[13]){
  char currentTag[13] = "000000000000";
  boolean reading = false;
  int i = 0;
  int readByte;
  char peekByte;
  if (ser.available() > 0){
    peekByte = ser.peek(); //peep next available byte
    if (peekByte == 2) {
      readByte = ser.read();
      reading = true; //begining of tag
      
      while (reading == true){
        readByte = ser.read();
        if (readByte == 3) {
          reading = false; //end of tag
          setTag(workingTag, currentTag);
        }

        else if (readByte != 10 && readByte != 13) {
          //store the tag
          if (i<sizeof(currentTag)){
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

int closeDoor(Servo servo, int servonum){
  int pos = servo.read();
  int closed = 0;
  float forceInit = currentForce(servonum);
  float forceNow = 0.0;
  //don't bother checking force at beginning and end
  for (int theta=pos; theta<highWrite-3; theta+=3){
    
    if (theta<lowWrite+6 || theta>highWrite-3){
      servo.write(theta);
      delay(15);
      closed = 1;
    }
    

    
    else{
        servo.write(theta);
        delay(15);
        forceNow = currentForce(servonum) - forceInit;
      if (forceNow > 5.0) {
        //reopen door
        servo.write(lowWrite);
        //print serial message that close door failed
        Serial.print("obstruction encountered! Initforce: ");
        Serial.print(forceInit);
        Serial.print(" forceNow: ");
        Serial.println(forceNow);
        return 0;
      }
    }
  }
  //Serial.print("initForce ");
  //Serial.println(forceInit);
  return 1;
}

void openDoor(Servo servo){
  int pos = servo.read();
  for (int theta=pos; theta>lowWrite+3; theta-=3){
    servo.write(theta);
    delay(15);
  }
}


float currentForce(int doornum) 
{
  int fsrADC;
  if (doornum == 1){
    fsrADC = analogRead(FSR_PIN1);
  }
  else if (doornum ==2){
    
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
    float force;
    // Break parabolic curve down into two linear slopes:
    if (fsrR <= 600) 
      force = (fsrG - 0.00075) / 0.00000032639;
    else
      force =  fsrG / 0.000000642857;
    return force;

  }
  else
  {
    //
    return 0;
  }
}
