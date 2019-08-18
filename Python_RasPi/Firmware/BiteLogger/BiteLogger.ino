/*
 * 
 * BiteLogger 06/15/19
  SD card datalogger

 This example shows how to log data from three analog sensors
 to an SD card using the SD library.

 The circuit:
 * analog sensors on analog ins 0, 1, and 2
 * SD card attached to SPI bus as follows:
 ** MOSI - pin 11
 ** MISO - pin 12
 ** CLK - pin 13
 ** CS - pin 4 (for MKRZero SD: SDCARD_SS_PIN)

 created  24 Nov 2010
 modified 9 Apr 2012
 by Tom Igoe

 This example code is in the public domain.

 */

#include <SPI.h>
#include <SD.h>

const int chipSelect = 8;
const int numTimeBytes = 13;
const char beginLogMsg[14] = "begin logging";
const char endLogMsg[12] = "end logging";

unsigned long previousMicros;
unsigned long currentMicros;
unsigned long stamp;
int fileTag = 0;
long interval = 500; //Microseconds
char zeroTime[14] = "0000000000000";
char timeChar[14];
char fileName[10] = "log00.txt";


void setTime(char newTime[14]){
  for (int i=0; i<numTimeBytes; i++){
    timeChar[i] = newTime[i];
  }
}

void clearTime() {
  setTime(zeroTime);
}

void setup() {
  // Open serial communications and wait for port to open:
  Serial.begin(9600);
  clearTime();
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }


  Serial.print("Initializing SD card...");

  // see if the card is present and can be initialized:
  if (!SD.begin(chipSelect)) {
    Serial.println("Card failed, or not present");
    // don't do anything more:
    while (1);
  }
  Serial.println("card initialized.");
}

void loop() {
  boolean logging = false;
  if (Serial.available() >= 2) {
    char commandRead = Serial.read();
    //CHECKING FOR LOG COMMAND
    if (commandRead != '4') {
      commandRead = 0;
    }
    else{
      char idRead = Serial.read();
      if (idRead != '1') {
        idRead = 0;
      }
        else{
        
        previousMicros = micros();
        int byteCount = 0;
        while (byteCount < numTimeBytes){
          char readByte = Serial.read();
          if (isDigit(readByte)){
            timeChar[byteCount] = readByte;
            byteCount += 1;
          }
        }
        // open the file. note that only one file can be open at a time,
        // so you have to close this one before opening another.
        int fileTag = 0;
        fileName[3] = '0';
        fileName[4] = '0';
        while (SD.exists(fileName)){
          fileTag += 1;
          char digOnes[2];
          char digTens[2];
          int ones = fileTag % 10;
          int tens = 0.1*(fileTag - ones);
          String strOnes = String(ones);
          String strTens = String(tens);
          strOnes.toCharArray(digOnes,2);
          strTens.toCharArray(digTens,2);
          fileName[3] = digTens[0];
          fileName[4] = digOnes[0];
        }
        logging = true;
        //print message
        Serial.println(beginLogMsg);
        File dataFile = SD.open(fileName, FILE_WRITE);
        dataFile.println(timeChar);

        while (logging==true) {
          currentMicros = micros();
          stamp = (unsigned long)(currentMicros - previousMicros);
          //if actual sampling rate slower than desired sampling
          //rate, write sample immediately
          if (stamp >= interval){
            previousMicros = currentMicros;
            // make a string for assembling the data to log:
            String dataString = String(stamp);
            dataString += ",";
            // read three sensors and append to the string:
            for (int analogPin = 0; analogPin < 2; analogPin++) {
              int sensor = analogRead(analogPin);
              dataString += String(sensor, DEC);
              if (analogPin < 1) {
                dataString += ",";
              }
            }

            // if the file is available, write to it:
            if (dataFile) {
              dataFile.println(dataString);
              
            }
            // if the file isn't open, pop up an error:
            else {
              Serial.print("error opening '");
              Serial.print(fileName);
              Serial.println("'");
            }

        }
        //if actual sampling rate faster than desired sampling
        //rate, delay
        else{
          unsigned long delayMicros = interval - stamp;
          delayMicroseconds(delayMicros);
        }
        
          //Check for end msg
          if (Serial.available() >= 2) {
    commandRead = Serial.read();
    //CHECKING FOR LOG COMMAND
    if (commandRead != '4') {
      commandRead = 0;
    }
    else{
      char idRead = Serial.read();
      if (idRead != '0') {
        idRead = 1;
      }
        else{
                logging = false;
              dataFile.close();
                Serial.println(endLogMsg);
                commandRead = 0;
                idRead = 0;
              }
            }
          }
      }
    }
  }
}
    delay(10);
}
