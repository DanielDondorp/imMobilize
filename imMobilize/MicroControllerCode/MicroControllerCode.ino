#include <Adafruit_NeoPixel.h>
#include <OneWire.h> 
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 2
#define PIN            4
#define NUMPIXELS      16

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

int r, g, b;
int freq, duration;
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
int sending_time, now;
int white_light = 5;
int ir_leds = 9;
int vibration_motor = 3;
double t1, t2;
void setup() {
  // initialize serial:
  setPwmFrequency(ir_leds, 1);
  
  Serial.begin(115200);
  Serial.setTimeout(10);
  
  pinMode(white_light, OUTPUT);
  pinMode(ir_leds, OUTPUT);
  pinMode(vibration_motor, OUTPUT);
  digitalWrite(white_light, LOW);
  sending_time = millis();
  now = millis();

  sensors.begin();

  sensors.setResolution(10);
  pixels.begin();
  pixels.clear();
  pixels.show();
}

void loop() {
  // print the string when a newline arrives:
 if(Serial.available()){
    inputString = Serial.readString();
    
    Serial.flush();
    if(inputString.startsWith("n")){
      if(inputString.startsWith("nC")){
        pixels.clear();
        pixels.show();
      }
      else{
      r = inputString.substring(1,4).toInt();
      g = inputString.substring(4,7).toInt();
      b = inputString.substring(7,11).toInt();
      for(int i=0;i<NUMPIXELS;i++){
         pixels.setPixelColor(i, pixels.Color(r,g,b)); 
         }
      pixels.show();
     }
   }
   else if(inputString.startsWith("wS")){
    digitalWrite(white_light, HIGH);
   }
   else if(inputString.startsWith("wC")){
    digitalWrite(white_light, LOW);
   }
   else if(inputString.startsWith("i")){
    int val = inputString.substring(1,4).toInt();
    analogWrite(ir_leds, val);
   }

   else if(inputString.startsWith("v")){
      freq = inputString.substring(1,4).toInt();
      duration = inputString.substring(4,8).toInt();
      tone(vibration_motor, freq, duration);
    }
 }
 //clear the string:
 inputString = ""; 
 
 now = millis();
 if(now - sending_time >= 1000){
   sensors.requestTemperatures();
   t1 = sensors.getTempCByIndex(0);
   t2 = sensors.getTempCByIndex(1);
   Serial.print(t1);
   Serial.print(" ");
   Serial.println(t2);
   sending_time = millis();
 }  
}

void setPwmFrequency(int pin, int divisor) {
  byte mode;
  if(pin == 5 || pin == 6 || pin == 9 || pin == 10) {
    switch(divisor) {
      case 1: mode = 0x01; break;
      case 8: mode = 0x02; break;
      case 64: mode = 0x03; break;
      case 256: mode = 0x04; break;
      case 1024: mode = 0x05; break;
      default: return;
    }
    if(pin == 5 || pin == 6) {
      TCCR0B = TCCR0B & 0b11111000 | mode;
    } else {
      TCCR1B = TCCR1B & 0b11111000 | mode;
    }
  } else if(pin == 3 || pin == 11) {
    switch(divisor) {
      case 1: mode = 0x01; break;
      case 8: mode = 0x02; break;
      case 32: mode = 0x03; break;
      case 64: mode = 0x04; break;
      case 128: mode = 0x05; break;
      case 256: mode = 0x06; break;
      case 1024: mode = 0x07; break;
      default: return;
    }
    TCCR2B = TCCR2B & 0b11111000 | mode;
  }
}

