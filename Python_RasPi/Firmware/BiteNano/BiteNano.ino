/*
  11/08/19

  Reads an analog input on pin 0, prints the result to the Serial Monitor.
  Graphical representation is available using Serial Plotter (Tools > Serial Plotter menu).
  Attach the center pin of a potentiometer to pin A0, and the outside pins to +5V and ground.

  This example code is in the public domain.

  http://www.arduino.cc/en/Tutorial/AnalogReadSerial
*/
#include <Servo.h>
const int analogInPin0 = A0;
const int digitalOutPin2 = 2;
const int away = 40;
const int near = 25;
const int servoPin = 12;
const int trialPin = 13;

float epsilon = 0.0002;
bool biting = false;
bool inTrial = false;
int bpodOut = 1;
float baseline;
float v;
float v0;
float thresh;
float marg;
float digOut = 0;
float diff = 0;

Servo biteServo;

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(115200);
  baseline = analogRead(A0);
  pinMode(digitalOutPin2, OUTPUT);
  pinMode(trialPin, INPUT);
  biteServo.attach(servoPin, 400, 1050);
  delay(500);
}

// the loop routine runs over and over again forever:
void loop() {
  
  bpodOut = digitalRead(trialPin);
  if (bpodOut < 1){
    if (inTrial == false){
      biteServo.write(near);
      delay(100);
      inTrial = true;
    }
  }
  if (bpodOut > 0) {
    if (inTrial == true){
      biteServo.write(away);
      delay(100);
      inTrial = false;
    }
  }
  // read the input on analog pin 0:
  v = analogRead(A0);
  v0 = (1 - epsilon)*baseline + epsilon*v;
  baseline = v0;
  thresh = 0.1*baseline;
  marg = 0.001*baseline;
  diff = baseline - v;
  if (biting) {
    if (diff < thresh - marg){
      biting = false;
      digitalWrite(digitalOutPin2, LOW);
    }
  }
  else {
    if (diff > thresh + marg){
      biting = true;
      digitalWrite(digitalOutPin2, HIGH);
    }
  }
  digOut = biting*1023;
  // print out the value you read:
  Serial.print(bpodOut);
  Serial.print(", ");
  Serial.print(v);
  Serial.print(", ");
  Serial.print(digOut);
  Serial.print(", ");
  Serial.print(baseline);
  Serial.print(", ");
  Serial.println(thresh+marg);
  delayMicroseconds(500);        // delay in between reads for stability
}
