#include <Adafruit_NeoPixel.h>


#include <OneWire.h> 
#include <DallasTemperature.h>

#define ONE_WIRE_BUS 3

#define PIN            4
#define NUMPIXELS      16

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

int r, g, b;
String inputString = "";         // a string to hold incoming data
boolean stringComplete = false;  // whether the string is complete
int sending_time, now;
int white_light = 7;
double t1, t2;
void setup() {
  // initialize serial:
  Serial.begin(115200);
  Serial.setTimeout(10);
  
  pinMode(white_light, OUTPUT);
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
         // clear the string:
      inputString = ""; 
 }
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
