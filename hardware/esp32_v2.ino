
#include "secrets.h"

#define BLYNK_TEMPLATE_ID   BLYNK_TEMPLATE_ID
#define BLYNK_TEMPLATE_NAME BLYNK_TEMPLATE_NAME


// ==========================================================
// LIBRARIES
// ==========================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <BlynkSimpleEsp32.h>


// ==========================================================
// CONFIGURATION
// ==========================================================

const char* WIFI_SSID     = WIFI_SSID_VALUE;
const char* WIFI_PASSWORD = WIFI_PASSWORD_VALUE;

const char* SERVER     = "http://" SERVER_HOST ":" SERVER_PORT "/ingest";
const char* COW_SERVER = "http://" SERVER_HOST ":" SERVER_PORT "/cows";


// ==========================================================
// SENSOR PINS
// ==========================================================

#define DHTPIN       16
#define DHTTYPE      DHT22
#define TDS_PIN      34
#define ONE_WIRE_BUS 4
#define BUTTON_PIN   27


// ==========================================================
// SENSOR OBJECTS
// ==========================================================

DHT dht(DHTPIN, DHTTYPE);
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature ds18b20(&oneWire);


// ==========================================================
// ADC / TDS CONFIGURATION
// ==========================================================

#define VREF                3.3
#define ADC_MAX             4095.0
#define FRESH_MILK_VOLTAGE  1.426
#define NUM_TDS_READINGS    5


// ==========================================================
// BACKEND VALIDATION LIMITS
// Must match config.py SENSOR_LIMITS exactly, otherwise the
// backend rejects the reading with HTTP 422.
// ==========================================================

#define MILK_TEMP_MIN   20.0    // config.py: (20, 45)
#define MILK_TEMP_MAX   45.0
#define COND_MIN        0.010   // config.py: (0.01, 30)
#define COND_MAX        30.0
#define YIELD_MAX       100.0   // config.py: (0, 100)


// ==========================================================
// DEMO DATE CONFIGURATION
// ==========================================================

const int START_YEAR  = 2026;
const int START_MONTH = 9;
const int START_DAY   = 1;
const int DEMO_HOUR   = 10;
const int DEMO_MINUTE = 0;


// ==========================================================
// GLOBAL VARIABLES
// ==========================================================

String cowID = "";
int  cowParity = 0;
bool cowRegistered = false;
int  demoDay = 1;

bool lastButtonState = HIGH;
unsigned long lastButtonTime = 0;
const unsigned long BUTTON_DEBOUNCE = 500;


// ==========================================================
// FUNCTION DECLARATIONS
// ==========================================================

void  connectWiFi();
bool  registerCowOnServer(String cowId, int parity);
void  createNewCow();
float readTDSAverage();
String getDemoDate();
void  takeMeasurement();
void  checkSerialCommands();
String readSerialLine();


// ==========================================================
// SETUP
// ==========================================================

void setup() {

  Serial.begin(115200);
  delay(1000);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  dht.begin();
  ds18b20.begin();

  connectWiFi();

  Serial.println();
  Serial.println("Connecting to Blynk...");
  Blynk.begin(BLYNK_AUTH_TOKEN, WIFI_SSID, WIFI_PASSWORD);
  Serial.println("Blynk Connected!");

  Serial.println();
  Serial.println("========================================");
  Serial.println("       MASTISENSE MASTITIS MONITOR");
  Serial.println("========================================");
  Serial.println();
  Serial.println("Enter a NEW cow.");
  Serial.println("The ESP32 will register it in the backend.");
  Serial.println();

  createNewCow();
}


// ==========================================================
// MAIN LOOP
// ==========================================================

void loop() {

  Blynk.run();

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected.");
    connectWiFi();
  }

  checkSerialCommands();

  bool buttonState = digitalRead(BUTTON_PIN);

  if (buttonState == LOW &&
      lastButtonState == HIGH &&
      millis() - lastButtonTime > BUTTON_DEBOUNCE) {

    lastButtonTime = millis();

    if (!cowRegistered) {
      Serial.println();
      Serial.println("========================================");
      Serial.println("       COW NOT REGISTERED");
      Serial.println("========================================");
      Serial.println("Please register a cow first (type NEW).");
      Serial.println("========================================");
    }
    else {
      takeMeasurement();
    }
  }

  lastButtonState = buttonState;
  delay(20);
}


// ==========================================================
// SERIAL HELPER
// ==========================================================

String readSerialLine() {

  while (Serial.available() == 0) {
    Blynk.run();
    delay(10);
  }

  String s = Serial.readStringUntil('\n');
  s.trim();
  return s;
}


// ==========================================================
// CONNECT WIFI
// ==========================================================

void connectWiFi() {

  Serial.println();
  Serial.println("========================================");
  Serial.println("        CONNECTING TO WIFI");
  Serial.println("========================================");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;

  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("WiFi Connected!");
    Serial.print("ESP32 IP : "); Serial.println(WiFi.localIP());
    Serial.print("Gateway  : "); Serial.println(WiFi.gatewayIP());
    Serial.print("Server   : "); Serial.println(SERVER);
  }
  else {
    Serial.println("WiFi connection FAILED.");
    Serial.println("Check WiFi SSID/password in secrets.h.");
  }
}


// ==========================================================
// REGISTER COW  —  POST /cows
// ==========================================================

bool registerCowOnServer(String cowId, int parity) {

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi is not connected.");
    return false;
  }

  WiFiClient client;
  HTTPClient http;

  Serial.println();
  Serial.println("========================================");
  Serial.println("       REGISTERING NEW COW");
  Serial.println("========================================");
  Serial.print("Cow ID : "); Serial.println(cowId);
  Serial.print("Parity : "); Serial.println(parity);
  Serial.print("Server : "); Serial.println(COW_SERVER);

  String body = "{";
  body += "\"cow_id\":\""; body += cowId; body += "\",";
  body += "\"parity\":";   body += String(parity);
  body += "}";

  Serial.println();
  Serial.println("JSON TO SERVER:");
  Serial.println(body);

  http.begin(client, COW_SERVER);
  http.setTimeout(15000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Accept", "application/json");

  Serial.println();
  Serial.println("Sending POST /cows...");

  int httpCode = http.POST(body);

  Serial.print("HTTP Response Code: ");
  Serial.println(httpCode);

  if (httpCode > 0) {

    String response = http.getString();

    Serial.println();
    Serial.println("========================================");
    Serial.println("       COW SERVER RESPONSE");
    Serial.println("========================================");
    Serial.println(response);

    if (httpCode >= 200 && httpCode < 300) {
      Serial.println();
      Serial.println("       COW CREATED SUCCESSFULLY");
      Serial.println("========================================");
      http.end();
      return true;
    }

    Serial.println();
    Serial.println("       COW REGISTRATION FAILED");

    if (httpCode == 400) {
      Serial.println("HTTP 400 — check Cow ID and parity.");
    }
    else if (httpCode == 404) {
      Serial.println("POST /cows not found — check FastAPI.");
    }
    else if (httpCode == 409) {
      Serial.println("Cow already exists.");
    }

    Serial.println("========================================");
  }
  else {
    Serial.println();
    Serial.println("========================================");
    Serial.println("       CONNECTION ERROR");
    Serial.println("========================================");
    Serial.print("HTTP error: ");
    Serial.println(http.errorToString(httpCode));
    Serial.println();
    Serial.println("Check:");
    Serial.println("1. FastAPI is running");
    Serial.println("2. Laptop IP in secrets.h is correct");
    Serial.println("3. Port 8000 allowed through firewall");
    Serial.println("4. ESP32 and laptop on same WiFi/hotspot");
    Serial.println("========================================");
  }

  http.end();
  return false;
}


// ==========================================================
// CREATE NEW COW
// ==========================================================

void createNewCow() {

  cowRegistered = false;

  Serial.println();
  Serial.println("========================================");
  Serial.println("          CREATE NEW COW");
  Serial.println("========================================");
  Serial.println();
  Serial.println("Enter Cow ID (example: COW018),");
  Serial.println("then press ENTER.");

  cowID = readSerialLine();

  if (cowID.length() == 0) {
    Serial.println("Invalid Cow ID.");
    return;
  }

  Serial.println();
  Serial.print("Cow ID entered: ");
  Serial.println(cowID);

  Serial.println();
  Serial.println("Enter Cow Parity (lactation number).");
  Serial.println("1 = First, 2 = Second, 3 = Third ...");
  Serial.println("Press ENTER after entering parity.");

  String parityInput = readSerialLine();
  cowParity = parityInput.toInt();

  if (cowParity <= 0) {
    Serial.println();
    Serial.println("Invalid parity. Cow was NOT registered.");
    return;
  }

  Serial.println();
  Serial.println("========================================");
  Serial.println("       COW INFORMATION");
  Serial.println("========================================");
  Serial.print("Cow ID : "); Serial.println(cowID);
  Serial.print("Parity : "); Serial.println(cowParity);
  Serial.println("========================================");

  cowRegistered = registerCowOnServer(cowID, cowParity);

  // Restart the demo timeline for each newly registered cow
  // so its readings begin at day 1 rather than continuing
  // from the previous cow's day counter.
  if (cowRegistered) {

    demoDay = 1;

    Serial.println();
    Serial.println("========================================");
    Serial.println("        MASTISENSE READY");
    Serial.println("========================================");
    Serial.print("Selected Cow      : "); Serial.println(cowID);
    Serial.print("Starting Demo Day : "); Serial.println(demoDay);
    Serial.println();
    Serial.println("PRESS BUTTON TO TAKE ONE SAMPLE");
    Serial.println();
    Serial.println("Each press will:");
    Serial.println("1. Ask milk yield");
    Serial.println("2. Ask SCC (optional - press ENTER to skip)");
    Serial.println("3. Read DHT22 (farm temp + humidity)");
    Serial.println("4. Read DS18B20 (milk temperature)");
    Serial.println("5. Read conductivity");
    Serial.println("6. Send JSON to /ingest");
    Serial.println("7. Print the returned risk forecast");
    Serial.println();
    Serial.println("Type NEW to register another cow.");
    Serial.println("========================================");
  }
  else {
    Serial.println();
    Serial.println("========================================");
    Serial.println("      COW WAS NOT REGISTERED");
    Serial.println("========================================");
    Serial.println("Check the backend response above.");
    Serial.println("========================================");
  }
}


// ==========================================================
// READ TDS SENSOR
// ==========================================================

float readTDSAverage() {

  long totalADC = 0;

  Serial.println();
  Serial.println("Taking 5 conductivity readings...");

  for (int i = 0; i < NUM_TDS_READINGS; i++) {

    int adcValue = analogRead(TDS_PIN);
    totalADC += adcValue;

    Serial.print("Reading ");
    Serial.print(i + 1);
    Serial.print(" : ");
    Serial.println(adcValue);

    delay(500);
  }

  return (float)totalADC / NUM_TDS_READINGS;
}


// ==========================================================
// DEMO DATE  —  with correct month rollover
// ==========================================================

String getDemoDate() {

  // Days in each month for the demo year.
  // (START_YEAR 2026 is not a leap year; February = 28.)
  const int daysInMonth[13] = {
    0, 31, 28, 31, 30, 31, 30,
    31, 31, 30, 31, 30, 31
  };

  int year  = START_YEAR;
  int month = START_MONTH;
  int day   = START_DAY + demoDay - 1;

  // Roll the day counter forward into the correct month/year
  // instead of producing invalid dates such as 2026-09-31.
  while (day > daysInMonth[month]) {

    day -= daysInMonth[month];
    month++;

    if (month > 12) {
      month = 1;
      year++;
    }
  }

  char buf[25];

  snprintf(
    buf,
    sizeof(buf),
    "%04d-%02d-%02dT%02d:%02d:00",
    year, month, day, DEMO_HOUR, DEMO_MINUTE
  );

  return String(buf);
}


// ==========================================================
// TAKE MEASUREMENT
// ==========================================================

void takeMeasurement() {

  Serial.println();
  Serial.println("========================================");
  Serial.println("       MEASUREMENT STARTED");
  Serial.println("========================================");


  // ========================================================
  // MILK YIELD (manual entry)
  // ========================================================

  Serial.println();
  Serial.println("========================================");
  Serial.println("          ENTER MILK YIELD");
  Serial.println("========================================");
  Serial.print("Cow ID: "); Serial.println(cowID);
  Serial.println();
  Serial.println("Enter milk yield in litres (example: 17.0)");
  Serial.println("Press ENTER after entering the value.");
  Serial.println();

  String yieldInput = readSerialLine();
  float milkYield = yieldInput.toFloat();

  if (milkYield <= 0 || milkYield > YIELD_MAX) {
    Serial.println();
    Serial.println("Invalid milk yield (must be 0 - 100 L).");
    Serial.println("Measurement cancelled.");
    return;
  }

  Serial.println();
  Serial.print("Milk Yield accepted: ");
  Serial.print(milkYield, 2);
  Serial.println(" L");


  // ========================================================
  // SCC (optional manual entry)
  //
  // SCC is a lab / cow-side test, not a continuous sensor.
  // Enter it only on days you actually measured it. On other
  // days press ENTER to skip: the backend carries the last
  // known value forward and tracks how stale it is.
  // ========================================================

  Serial.println();
  Serial.println("========================================");
  Serial.println("       ENTER SCC (OPTIONAL)");
  Serial.println("========================================");
  Serial.println("Enter SCC in cells/mL (example: 250000)");
  Serial.println("Press ENTER alone to SKIP (no test today).");
  Serial.println();

  String sccInput = readSerialLine();

  bool  hasSCC = (sccInput.length() > 0);
  float sccValue = 0.0;

  if (hasSCC) {

    sccValue = sccInput.toFloat();

    if (sccValue < 0 || sccValue > 20000000.0) {
      Serial.println("Invalid SCC value. Skipping SCC.");
      hasSCC = false;
    }
    else {
      Serial.print("SCC accepted: ");
      Serial.print(sccValue, 0);
      Serial.println(" cells/mL");
    }
  }
  else {
    Serial.println("SCC skipped for this reading.");
  }


  // ========================================================
  // DEMO DATE
  // ========================================================

  String timestamp = getDemoDate();

  Serial.println();
  Serial.print("Cow ID    : "); Serial.println(cowID);
  Serial.print("Demo Day  : "); Serial.println(demoDay);
  Serial.print("Demo Date : "); Serial.println(timestamp);


  // ========================================================
  // DHT22  —  FARM TEMPERATURE + HUMIDITY
  //
  // On failure we ABORT rather than sending 0.0, because a
  // fabricated 0 would corrupt the derived heat index.
  // ========================================================

  float farmTemperature = dht.readTemperature();
  float farmHumidity    = dht.readHumidity();

  bool hasFarmEnv = true;

  if (isnan(farmTemperature) || isnan(farmHumidity)) {

    Serial.println();
    Serial.println("WARNING: DHT22 read failed.");
    Serial.println("Farm temperature/humidity will be omitted.");
    Serial.println("The backend will use its baseline value.");

    hasFarmEnv = false;
  }


  // ========================================================
  // DS18B20  —  MILK TEMPERATURE  (REQUIRED)
  //
  // This one is mandatory: the backend rejects the whole
  // reading if milk_temp_c is outside 20-45 C, so sending a
  // failure value of 0.0 would lose the sample entirely.
  // ========================================================

  ds18b20.requestTemperatures();
  float milkTemperature = ds18b20.getTempCByIndex(0);

  if (milkTemperature == DEVICE_DISCONNECTED_C) {
    Serial.println();
    Serial.println("========================================");
    Serial.println("       DS18B20 READ FAILED");
    Serial.println("========================================");
    Serial.println("Milk temperature is required.");
    Serial.println("Check the sensor wiring on GPIO 4.");
    Serial.println("Measurement ABORTED (nothing sent).");
    Serial.println("Demo day NOT advanced.");
    Serial.println("========================================");
    return;
  }

  if (milkTemperature < MILK_TEMP_MIN ||
      milkTemperature > MILK_TEMP_MAX) {

    Serial.println();
    Serial.println("========================================");
    Serial.println("    MILK TEMPERATURE OUT OF RANGE");
    Serial.println("========================================");
    Serial.print("Measured: ");
    Serial.print(milkTemperature, 2);
    Serial.println(" C");
    Serial.print("Backend accepts: ");
    Serial.print(MILK_TEMP_MIN, 1);
    Serial.print(" - ");
    Serial.print(MILK_TEMP_MAX, 1);
    Serial.println(" C");
    Serial.println();
    Serial.println("The backend would reject this reading.");
    Serial.println("Measurement ABORTED (nothing sent).");
    Serial.println("========================================");
    return;
  }


  // ========================================================
  // TDS / CONDUCTIVITY
  // ========================================================

  float averageADC  = readTDSAverage();
  float milkVoltage = (averageADC / ADC_MAX) * VREF;

  float relativeECIndex = 0.0;

  if (FRESH_MILK_VOLTAGE > 0) {
    relativeECIndex = (milkVoltage / FRESH_MILK_VOLTAGE) * 100.0;
  }

  float tds = (milkVoltage / VREF) * 1000.0;
  float conductivity = tds / 500.0;

  if (conductivity < COND_MIN) conductivity = COND_MIN;
  if (conductivity > COND_MAX) conductivity = COND_MAX;


  // ========================================================
  // DISPLAY VALUES
  // ========================================================

  Serial.println();
  Serial.println("========================================");
  Serial.println("       AVERAGE SENSOR VALUES");
  Serial.println("========================================");
  Serial.print("Cow ID           : "); Serial.println(cowID);
  Serial.print("Demo Day         : "); Serial.println(demoDay);
  Serial.print("Demo Date        : "); Serial.println(timestamp);
  Serial.print("Milk Yield       : "); Serial.print(milkYield, 2);        Serial.println(" L");

  if (hasSCC) {
    Serial.print("SCC              : "); Serial.print(sccValue, 0);       Serial.println(" cells/mL");
  } else {
    Serial.println("SCC              : (not measured today)");
  }

  if (hasFarmEnv) {
    Serial.print("Farm Temperature : "); Serial.print(farmTemperature, 2); Serial.println(" C");
    Serial.print("Humidity         : "); Serial.print(farmHumidity, 2);    Serial.println(" %");
  } else {
    Serial.println("Farm Temp/Humid  : (sensor failed - omitted)");
  }

  Serial.print("Milk Temperature : "); Serial.print(milkTemperature, 2);  Serial.println(" C");
  Serial.print("Average ADC      : "); Serial.println(averageADC, 1);
  Serial.print("Milk Voltage     : "); Serial.print(milkVoltage, 4);      Serial.println(" V");
  Serial.print("Estimated TDS    : "); Serial.print(tds, 2);              Serial.println(" ppm");
  Serial.print("Estimated EC     : "); Serial.print(conductivity, 3);     Serial.println(" mS/cm");
  Serial.print("Relative EC Index: "); Serial.print(relativeECIndex, 2);  Serial.println(" %");


  // ========================================================
  // BLYNK
  // ========================================================

  if (hasFarmEnv) {
    Blynk.virtualWrite(V0, farmTemperature);
    Blynk.virtualWrite(V1, farmHumidity);
  }

  Blynk.virtualWrite(V2, milkTemperature);
  Blynk.virtualWrite(V3, conductivity);
  Blynk.virtualWrite(V4, tds);
  Blynk.virtualWrite(V5, relativeECIndex);

  Serial.println();
  Serial.println("Values sent to Blynk.");


  // ========================================================
  // CREATE JSON
  //
  // Only fields this hardware ACTUALLY measures are sent.
  // Everything else is omitted so the backend fills in its
  // documented prototype baselines on the correct scale.
  // ========================================================

  String body = "{";

  body += "\"cow_id\":\"";    body += cowID;     body += "\",";
  body += "\"timestamp\":\""; body += timestamp; body += "\",";

  body += "\"milk_yield_l\":";      body += String(milkYield, 2);      body += ",";
  body += "\"milk_conductivity\":"; body += String(conductivity, 3);   body += ",";
  body += "\"milk_temp_c\":";       body += String(milkTemperature, 2);

  // SCC only when actually measured.
  if (hasSCC) {
    body += ",\"scc_value\":";
    body += String(sccValue, 0);
  }

  // Raw environment readings. The backend derives
  // environment_heat_index from these two values itself, so
  // we deliberately do NOT send a heat index of our own.
  if (hasFarmEnv) {
    body += ",\"farm_temperature_c\":";
    body += String(farmTemperature, 2);

    body += ",\"farm_humidity\":";
    body += String(farmHumidity, 2);
  }

  body += ",\"source\":\"esp32\"";
  body += "}";


  // ========================================================
  // DISPLAY JSON
  // ========================================================

  Serial.println();
  Serial.println("========================================");
  Serial.println("             JSON TO SERVER");
  Serial.println("========================================");
  Serial.println(body);

  Serial.println();
  Serial.print("Server: ");
  Serial.println(SERVER);
  Serial.println();
  Serial.println("Connecting to FastAPI /ingest...");


  // ========================================================
  // SEND POST /ingest
  // ========================================================

  WiFiClient client;
  HTTPClient http;

  http.begin(client, SERVER);
  http.setTimeout(20000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Accept", "application/json");

  int httpCode = http.POST(body);

  Serial.println();
  Serial.print("HTTP Response Code: ");
  Serial.println(httpCode);


  // ========================================================
  // SERVER RESPONSE
  // ========================================================

  if (httpCode > 0) {

    String response = http.getString();

    Serial.println();
    Serial.println("========================================");
    Serial.println("          SERVER RESPONSE");
    Serial.println("========================================");
    Serial.println(response);


    if (httpCode >= 200 && httpCode < 300) {

      Serial.println();
      Serial.println("========================================");
      Serial.println("       SAMPLE ACCEPTED SUCCESSFULLY");
      Serial.println("========================================");
      Serial.print("Cow ID   : "); Serial.println(cowID);
      Serial.print("Demo Day : "); Serial.println(demoDay);


      // ----------------------------------------------------
      // Quick check that a validated model actually served a
      // prediction. If no model is promoted the backend
      // stores the reading but skips the forecast.
      // ----------------------------------------------------

      if (response.indexOf("\"model_status\":\"active\"") >= 0) {
        Serial.println();
        Serial.println("Prediction served by active model.");
        Serial.println("See risk_percent_7d / risk_percent_14d above.");
      }
      else if (response.indexOf("no_active_model") >= 0) {
        Serial.println();
        Serial.println("NOTE: Reading stored, but NO validated");
        Serial.println("model is promoted, so no risk forecast");
        Serial.println("was produced. Train/promote a model.");
      }

      demoDay++;

      Serial.println();
      Serial.print("Next Demo Day: ");
      Serial.println(demoDay);
      Serial.println("========================================");
    }

    else if (httpCode == 404) {

      Serial.println();
      Serial.println("========================================");
      Serial.println("       COW NOT REGISTERED");
      Serial.println("========================================");
      Serial.println("Backend says this cow is not registered.");
      Serial.println("Type NEW to register it again.");
      Serial.println("========================================");

      cowRegistered = false;
    }

    else if (httpCode == 422) {

      Serial.println();
      Serial.println("========================================");
      Serial.println("     READING REJECTED (VALIDATION)");
      Serial.println("========================================");
      Serial.println("A sensor value was outside the range the");
      Serial.println("backend accepts. See the response above.");
      Serial.println();
      Serial.println("Backend ranges (config.py SENSOR_LIMITS):");
      Serial.println("  milk_temp_c       : 20 - 45 C");
      Serial.println("  milk_conductivity : 0.01 - 30 mS/cm");
      Serial.println("  milk_yield_l      : 0 - 100 L");
      Serial.println("========================================");
      Serial.println("Demo day NOT advanced.");
    }

    else {

      Serial.println();
      Serial.println("========================================");
      Serial.println("       SERVER REJECTED REQUEST");
      Serial.println("========================================");
      Serial.println("Sample was NOT accepted.");
      Serial.println("Demo day NOT advanced.");
      Serial.println("========================================");
    }
  }

  else {

    Serial.println();
    Serial.println("========================================");
    Serial.println("       HTTP CONNECTION ERROR");
    Serial.println("========================================");
    Serial.print("Error: ");
    Serial.println(http.errorToString(httpCode));
    Serial.println();
    Serial.println("Check:");
    Serial.println("1. FastAPI is running");
    Serial.println("2. Laptop IP in secrets.h is correct");
    Serial.println("3. ESP32 and laptop on same hotspot");
    Serial.println("4. Windows Firewall allows port 8000");
    Serial.println("========================================");
    Serial.println();
    Serial.println("Sample was NOT accepted.");
    Serial.println("Demo day NOT advanced.");
  }

  http.end();

  Serial.println();
  Serial.println("Waiting for next button press...");
}


// ==========================================================
// SERIAL COMMANDS
// ==========================================================

void checkSerialCommands() {

  if (Serial.available() == 0) {
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();

  if (command == "NEW") {
    Serial.println();
    Serial.println("========================================");
    Serial.println("       NEW COW REQUESTED");
    Serial.println("========================================");
    Serial.println();
    createNewCow();
    return;
  }

  if (command.length() > 0) {
    Serial.println();
    Serial.println("Unknown command.");
    Serial.println("Type NEW to register another cow.");
  }
}