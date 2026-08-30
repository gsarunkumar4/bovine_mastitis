#include <WiFi.h>
#include <HTTPClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

const char* WIFI_SSID="YOUR_HOTSPOT";
const char* WIFI_PASSWORD="YOUR_PASSWORD";
const char* SERVER="http://YOUR_LAPTOP_IP:8000/ingest";
#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// One daily sample is the intended prototype workflow.
// For a fast demo, temporarily change this to 10000UL (10 seconds).
const unsigned long SAMPLE_INTERVAL_MS = 86400000UL;
unsigned long lastSample = 0;

void sendSample(){
  sensors.requestTemperatures();
  float tempC=sensors.getTempCByIndex(0);

  // Replace these two values with calibrated sensor readings.
  float conductivity=4.8;
  float milkYieldL=14.0;

  String body=String("{\"cow_id\":\"cow_001\",\"milk_yield_l\":")+String(milkYieldL,2)+
    ",\"milk_conductivity\":"+String(conductivity,2)+
    ",\"milk_temp_c\":"+String(tempC,2)+",\"source\":\"esp32\"}";

  if(WiFi.status()==WL_CONNECTED){
    HTTPClient http;
    http.begin(SERVER);
    http.addHeader("Content-Type","application/json");
    int code=http.POST(body);
    Serial.println(code);
    Serial.println(http.getString());
    http.end();
  }
}

void setup(){
  Serial.begin(115200);
  sensors.begin();
  WiFi.begin(WIFI_SSID,WIFI_PASSWORD);
  while(WiFi.status()!=WL_CONNECTED){delay(500);Serial.print(".");}
  Serial.println("\nConnected");
  sendSample();
  lastSample=millis();
}

void loop(){
  if(millis()-lastSample >= SAMPLE_INTERVAL_MS){
    sendSample();
    lastSample=millis();
  }
  delay(1000);
}
