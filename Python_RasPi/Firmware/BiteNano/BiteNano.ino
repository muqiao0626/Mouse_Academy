/*
  AnalogReadSerial

  Reads an analog input on pin 0, prints the result to the Serial Monitor.
  Graphical representation is available using Serial Plotter (Tools > Serial Plotter menu).
  Attach the center pin of a potentiometer to pin A0, and the outside pins to +5V and ground.

  This example code is in the public domain.

  http://www.arduino.cc/en/Tutorial/AnalogReadSerial
*/
const int analogInPin0 = A0;
const int digitalOutPin2 = 2;

float epsilon = 0.002;
bool biting = false;
float baseline;
float v;
float v0;
float thresh;
float marg;
float digOut = 0;
float diff = 0;

// the setup routine runs once when you press reset:
void setup() {
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  baseline = analogRead(A0);
  pinMode(digitalOutPin2, OUTPUT);
}

// the loop routine runs over and over again forever:
void loop() {
  // read the input on analog pin 0:
  v = analogRead(A0);
  v0 = (1 - epsilon)*baseline + epsilon*v;
  baseline = v0;
  thresh = 0.03*baseline;
  marg = 0.01*baseline;
  diff = baseline - v;
  if (biting) {
    if (diff < thresh - marg){
      biting = false;
    }
  }
  else {
    if (diff > thresh + marg){
      biting = true;
    }
  }
  digOut = biting*1023;
  // print out the value you read:
  Serial.print(v);
  Serial.print(", ");
  Serial.print(digOut);
  Serial.print(", ");
  Serial.print(baseline);
  Serial.print(", ");
  Serial.println(thresh+marg);
  delayMicroseconds(500);        // delay in between reads for stability
}
