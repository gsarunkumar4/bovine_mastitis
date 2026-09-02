#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// =================================================
// WIFI
// =================================================

const char* WIFI_SSID = "realme";
const char* WIFI_PASSWORD = "anbc8928";

const char* SERVER =
  "http://10.93.225.40:8000/ingest";


// =================================================
// COW ID
// =================================================
//
// Cow ID is entered through Serial Monitor.
//
// Example:
// COW001
// COW002
// COW101
//
// The same ESP32 can therefore be used for
// multiple cows.
// =================================================

String COW_ID = "";


// =================================================
// SENSOR PINS
// =================================================

#define DHT_PIN 16
#define DHT_TYPE DHT22

#define TDS_PIN 34

#define DS18B20_PIN 4

#define BUTTON_PIN 27


// =================================================
// ADC SETTINGS
// =================================================

#define VREF 3.3
#define ADC_MAX 4095.0

#define NUM_READINGS 5


// =================================================
// MILK REFERENCE
// =================================================

#define FRESH_MILK_VOLTAGE 1.426


// =================================================
// OBJECTS
// =================================================

DHT dht(DHT_PIN, DHT_TYPE);

OneWire oneWire(DS18B20_PIN);

DallasTemperature milkTempSensor(&oneWire);


// =================================================
// BUTTON
// =================================================

bool lastButtonState = HIGH;


// =================================================
// SERIAL COW ID INPUT
// =================================================

String serialInput = "";


// =================================================
// DEMO DATE
// =================================================
//
// Every successful button press advances by one day.
//
// Day 1  -> 2026-09-01
// Day 2  -> 2026-09-02
// Day 3  -> 2026-09-03
// ...
// Day 14 -> 2026-09-14
//
// This is ONLY for accelerated demonstration.
// =================================================

int demoDay = 1;

const int DEMO_START_YEAR = 2026;
const int DEMO_START_MONTH = 9;
const int DEMO_START_DAY = 1;


// =================================================
// DAYS IN MONTH
// =================================================

int daysInMonth(int year, int month)
{
  if (month == 2)
  {
    if (
      (year % 400 == 0) ||
      ((year % 4 == 0) && (year % 100 != 0))
    )
    {
      return 29;
    }

    return 28;
  }

  if (
    month == 4 ||
    month == 6 ||
    month == 9 ||
    month == 11
  )
  {
    return 30;
  }

  return 31;
}


// =================================================
// CREATE DEMO DATE
// =================================================

String getDemoDate()
{
  int year = DEMO_START_YEAR;
  int month = DEMO_START_MONTH;
  int day = DEMO_START_DAY;

  int remaining = demoDay - 1;

  while (remaining > 0)
  {
    day++;

    if (day > daysInMonth(year, month))
    {
      day = 1;
      month++;

      if (month > 12)
      {
        month = 1;
        year++;
      }
    }

    remaining--;
  }

  char dateBuffer[20];

  sprintf(
    dateBuffer,
    "%04d-%02d-%02dT10:00:00",
    year,
    month,
    day
  );

  return String(dateBuffer);
}


// =================================================
// READ TDS AVERAGE
// =================================================

float readTDSAverage()
{
  long total = 0;

  for (int i = 0; i < NUM_READINGS; i++)
  {
    int adc = analogRead(TDS_PIN);

    total += adc;

    Serial.print("Reading ");
    Serial.print(i + 1);
    Serial.print(" : ");
    Serial.println(adc);

    delay(500);
  }

  return total / (float)NUM_READINGS;
}


// =================================================
// SERIAL COW ID INPUT
// =================================================
//
// Type a Cow ID in Serial Monitor and press Enter.
//
// Example:
// COW001
//
// The ID is immediately updated.
// =================================================

void checkSerialCowID()
{
  while (Serial.available() > 0)
  {
    char incomingChar = Serial.read();

    // ------------------------------------------------
    // ENTER KEY
    // ------------------------------------------------

    if (
      incomingChar == '\n' ||
      incomingChar == '\r'
    )
    {
      if (serialInput.length() > 0)
      {
        serialInput.trim();

        if (serialInput.length() > 0)
        {
          COW_ID = serialInput;

          Serial.println();
          Serial.println("========================================");
          Serial.println("          COW ID UPDATED");
          Serial.println("========================================");

          Serial.print("Selected Cow ID: ");
          Serial.println(COW_ID);

          Serial.println();
          Serial.println("Next sensor reading will be stored");
          Serial.println("for this cow.");

          Serial.println("========================================");
          Serial.println();

          serialInput = "";
        }
      }
    }

    // ------------------------------------------------
    // NORMAL CHARACTER
    // ------------------------------------------------

    else
    {
      serialInput += incomingChar;
    }
  }
}


// =================================================
// WAIT FOR COW ID
// =================================================

void waitForCowID()
{
  Serial.println();
  Serial.println("========================================");
  Serial.println("       BOVINE MASTITIS MONITOR");
  Serial.println("========================================");

  Serial.println();
  Serial.println("Enter Cow ID using Serial Monitor.");
  Serial.println("Example: COW001");
  Serial.println("Then press ENTER.");
  Serial.println();

  while (COW_ID.length() == 0)
  {
    checkSerialCowID();

    delay(10);
  }

  Serial.println();
  Serial.println("========================================");
  Serial.println("       COW ID SELECTED");
  Serial.println("========================================");

  Serial.print("Cow ID: ");
  Serial.println(COW_ID);

  Serial.println("========================================");
  Serial.println();
}


// =================================================
// SEND SAMPLE
// =================================================

void collectAndSend()
{
  Serial.println();
  Serial.println("========================================");
  Serial.println("       MEASUREMENT STARTED");
  Serial.println("========================================");


  // ------------------------------------------------
  // COW ID CHECK
  // ------------------------------------------------

  if (COW_ID.length() == 0)
  {
    Serial.println("ERROR: Cow ID not selected.");

    Serial.println("Enter Cow ID in Serial Monitor.");

    return;
  }


  // ------------------------------------------------
  // DEMO DATE
  // ------------------------------------------------

  String demoDate = getDemoDate();

  Serial.print("Cow ID   : ");
  Serial.println(COW_ID);

  Serial.print("Demo Day : ");
  Serial.println(demoDay);

  Serial.print("Demo Date: ");
  Serial.println(demoDate);


  // ------------------------------------------------
  // DHT22 FARM ENVIRONMENT
  // ------------------------------------------------

  float farmTemperature =
    dht.readTemperature();

  float humidity =
    dht.readHumidity();


  // ------------------------------------------------
  // DS18B20 MILK TEMPERATURE
  // ------------------------------------------------

  milkTempSensor.requestTemperatures();

  float milkTemperature =
    milkTempSensor.getTempCByIndex(0);


  // ------------------------------------------------
  // TDS / CONDUCTIVITY SENSOR
  // ------------------------------------------------

  Serial.println();
  Serial.println("Taking 5 conductivity readings...");

  float averageADC =
    readTDSAverage();


  // ------------------------------------------------
  // ADC -> VOLTAGE
  // ------------------------------------------------

  float milkVoltage =
    (averageADC / ADC_MAX) * VREF;


  // ------------------------------------------------
  // VOLTAGE -> RELATIVE ELECTRICAL INDEX
  // ------------------------------------------------

  float relativeIndex =
    (milkVoltage / FRESH_MILK_VOLTAGE) * 100.0;


  // ------------------------------------------------
  // VOLTAGE -> APPROXIMATE TDS
  // ------------------------------------------------

  float tds =
    (milkVoltage / VREF) * 1000.0;


  // ------------------------------------------------
  // TDS -> APPROXIMATE CONDUCTIVITY
  // ------------------------------------------------

  float conductivity =
    tds / 500.0;


  if (conductivity < 0.01)
  {
    conductivity = 0.01;
  }


  if (conductivity > 30.0)
  {
    conductivity = 30.0;
  }


  // =================================================
  // DISPLAY SENSOR VALUES
  // =================================================

  Serial.println();
  Serial.println("========================================");
  Serial.println("       AVERAGE SENSOR VALUES");
  Serial.println("========================================");


  Serial.print("Cow ID           : ");
  Serial.println(COW_ID);


  Serial.print("Demo Day         : ");
  Serial.println(demoDay);


  Serial.print("Demo Date        : ");
  Serial.println(demoDate);


  // ------------------------------------------------
  // FARM TEMPERATURE
  // ------------------------------------------------

  if (isnan(farmTemperature))
  {
    Serial.println("Farm Temperature : ERROR");
  }
  else
  {
    Serial.print("Farm Temperature : ");
    Serial.print(farmTemperature, 2);
    Serial.println(" °C");
  }


  // ------------------------------------------------
  // FARM HUMIDITY
  // ------------------------------------------------

  if (isnan(humidity))
  {
    Serial.println("Humidity         : ERROR");
  }
  else
  {
    Serial.print("Humidity         : ");
    Serial.print(humidity, 2);
    Serial.println(" %");
  }


  // ------------------------------------------------
  // MILK TEMPERATURE
  // ------------------------------------------------

  if (
    milkTemperature == DEVICE_DISCONNECTED_C ||
    isnan(milkTemperature)
  )
  {
    Serial.println("Milk Temperature : ERROR");
  }
  else
  {
    Serial.print("Milk Temperature : ");
    Serial.print(milkTemperature, 2);
    Serial.println(" °C");
  }


  // ------------------------------------------------
  // CONDUCTIVITY
  // ------------------------------------------------

  Serial.print("Average ADC      : ");
  Serial.println(averageADC, 1);


  Serial.print("Milk Voltage     : ");
  Serial.print(milkVoltage, 4);
  Serial.println(" V");


  Serial.print("Estimated TDS    : ");
  Serial.print(tds, 2);
  Serial.println(" ppm");


  Serial.print("Estimated EC     : ");
  Serial.print(conductivity, 3);
  Serial.println(" mS/cm");


  Serial.print("Relative EC Index: ");
  Serial.print(relativeIndex, 2);
  Serial.println(" %");


  // =================================================
  // JSON
  // =================================================

  String body = "{";


  // ------------------------------------------------
  // COW ID
  // ------------------------------------------------

  body += "\"cow_id\":\"";
  body += COW_ID;
  body += "\",";


  // ------------------------------------------------
  // TIMESTAMP
  // ------------------------------------------------

  body += "\"timestamp\":\"";
  body += demoDate;
  body += "\",";


  // ------------------------------------------------
  // MILK YIELD
  // ------------------------------------------------
  //
  // Current prototype uses fixed demo value.
  // ------------------------------------------------

  body += "\"milk_yield_l\":14.0,";


  // ------------------------------------------------
  // MILK CONDUCTIVITY
  // ------------------------------------------------

  body += "\"milk_conductivity\":";
  body += String(conductivity, 3);
  body += ",";


  // ------------------------------------------------
  // MILK TEMPERATURE
  // ------------------------------------------------

  body += "\"milk_temp_c\":";

  if (
    milkTemperature == DEVICE_DISCONNECTED_C ||
    isnan(milkTemperature)
  )
  {
    body += "null";
  }
  else
  {
    body += String(milkTemperature, 2);
  }

  body += ",";


  // =================================================
  // FARM TEMPERATURE
  // =================================================
  //
  // DHT22 actual temperature reading.
  // =================================================

  body += "\"farm_temperature_c\":";

  if (isnan(farmTemperature))
  {
    body += "null";
  }
  else
  {
    body += String(farmTemperature, 2);
  }

  body += ",";


  // =================================================
  // FARM HUMIDITY
  // =================================================
  //
  // DHT22 actual relative humidity reading.
  // =================================================

  body += "\"farm_humidity\":";

  if (isnan(humidity))
  {
    body += "null";
  }
  else
  {
    body += String(humidity, 2);
  }

  body += ",";


  // ------------------------------------------------
  // SOURCE
  // ------------------------------------------------

  body += "\"source\":\"esp32\"";


  // ------------------------------------------------
  // CLOSE JSON
  // ------------------------------------------------

  body += "}";


  // =================================================
  // SHOW JSON
  // =================================================

  Serial.println();
  Serial.println("========================================");
  Serial.println("             JSON SENT");
  Serial.println("========================================");

  Serial.println(body);


  // =================================================
  // SEND TO SERVER
  // =================================================

  bool success = false;


  if (WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;


    http.begin(SERVER);


    http.addHeader(
      "Content-Type",
      "application/json"
    );


    int httpCode =
      http.POST(body);


    Serial.print("HTTP Response: ");
    Serial.println(httpCode);


    if (httpCode > 0)
    {
      String response =
        http.getString();


      Serial.println();
      Serial.println("SERVER RESPONSE:");

      Serial.println(response);


      // ------------------------------------------------
      // HTTP 200 = SUCCESS
      // ------------------------------------------------

      if (httpCode == 200)
      {
        success = true;
      }
    }
    else
    {
      Serial.print("HTTP Error: ");

      Serial.println(
        http.errorToString(httpCode)
      );
    }


    http.end();
  }
  else
  {
    Serial.println(
      "WiFi disconnected!"
    );
  }


  // =================================================
  // ADVANCE DEMO DAY ONLY AFTER SUCCESS
  // =================================================

  if (success)
  {
    demoDay++;


    Serial.println();
    Serial.println("========================================");
    Serial.println("       SAMPLE SENT SUCCESSFULLY");
    Serial.println("========================================");


    Serial.print("Cow ID: ");
    Serial.println(COW_ID);


    Serial.print("Next Demo Day: ");
    Serial.println(demoDay);


    Serial.println("========================================");
  }
  else
  {
    Serial.println();
    Serial.println("========================================");
    Serial.println("       SAMPLE WAS NOT ACCEPTED");
    Serial.println("========================================");

    Serial.println("Demo day was NOT advanced.");

    Serial.println("Fix the connection and press");
    Serial.println("the button again.");

    Serial.println("========================================");
  }


  Serial.println();
  Serial.println(
    "Waiting for next button press..."
  );

  Serial.println();
}


// =================================================
// SETUP
// =================================================

void setup()
{
  Serial.begin(115200);

  delay(2000);


  // ------------------------------------------------
  // ADC
  // ------------------------------------------------

  analogReadResolution(12);


  // ------------------------------------------------
  // SENSORS
  // ------------------------------------------------

  dht.begin();

  milkTempSensor.begin();


  // ------------------------------------------------
  // BUTTON
  // ------------------------------------------------

  pinMode(
    BUTTON_PIN,
    INPUT_PULLUP
  );


  // ------------------------------------------------
  // WIFI
  // ------------------------------------------------

  Serial.println();

  Serial.println(
    "Connecting to WiFi..."
  );


  WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
  );


  while (
    WiFi.status() != WL_CONNECTED
  )
  {
    delay(500);

    Serial.print(".");
  }


  Serial.println();

  Serial.println(
    "WiFi Connected!"
  );


  // ------------------------------------------------
  // ESP32 IP
  // ------------------------------------------------

  Serial.print(
    "ESP32 IP: "
  );

  Serial.println(
    WiFi.localIP()
  );


  // ------------------------------------------------
  // COW ID
  // ------------------------------------------------

  waitForCowID();


  // ------------------------------------------------
  // READY
  // ------------------------------------------------

  Serial.println();

  Serial.println(
    "========================================"
  );

  Serial.println(
    "        ACCELERATED DEMO MODE"
  );

  Serial.println(
    "========================================"
  );


  Serial.print(
    "Selected Cow: "
  );

  Serial.println(
    COW_ID
  );


  Serial.print(
    "Starting Demo Day: "
  );

  Serial.println(
    demoDay
  );


  Serial.println();

  Serial.println(
    "PRESS BUTTON TO TAKE ONE SAMPLE"
  );


  Serial.println(
    "Each successful press = next demo day"
  );


  Serial.println();


  Serial.println(
    "To change Cow ID:"
  );

  Serial.println(
    "Type the new ID in Serial Monitor"
  );

  Serial.println(
    "and press ENTER."
  );


  Serial.println(
    "========================================"
  );
}


// =================================================
// LOOP
// =================================================

void loop()
{
  // ------------------------------------------------
  // CHECK FOR NEW COW ID
  // ------------------------------------------------

  checkSerialCowID();


  // ------------------------------------------------
  // BUTTON
  // ------------------------------------------------

  bool buttonState =
    digitalRead(BUTTON_PIN);


  // ------------------------------------------------
  // BUTTON PRESS
  // ------------------------------------------------

  if (
    lastButtonState == HIGH &&
    buttonState == LOW
  )
  {
    delay(50);


    if (
      digitalRead(BUTTON_PIN) == LOW
    )
    {
      collectAndSend();


      // ------------------------------------------------
      // WAIT UNTIL BUTTON IS RELEASED
      // ------------------------------------------------

      while (
        digitalRead(BUTTON_PIN) == LOW
      )
      {
        delay(10);
      }
    }
  }


  lastButtonState =
    buttonState;


  // ------------------------------------------------
  // WIFI RECONNECT
  // ------------------------------------------------

  if (
    WiFi.status() != WL_CONNECTED
  )
  {
    Serial.println("WiFi disconnected. Reconnecting...");

    WiFi.reconnect();

    delay(500);
  }


  delay(20);
}