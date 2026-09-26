// MastiSense MAIN ESP32 - Gateway + Milk/Farm Sensors
// Wireless link to Neckband ESP32: ESP-NOW
// Main -> FastAPI: Wi-Fi HTTP
//
// IMPORTANT:
// 1) Fill WIFI_SSID / WIFI_PASSWORD.
// 2) Set SERVER_HOST to the laptop running FastAPI.
// 3) Put the NECKBAND ESP32 MAC in NECKBAND_MAC.
// 4) This code keeps the original button -> manual yield/SCC ->
//    DHT22 -> milk DS18B20 -> conductivity -> /ingest workflow.
// 5) Body temperature and activity come from the neckband.
// 6) Activity algorithm is NOT run on this ESP32.

#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <SPI.h>
#include <MFRC522.h>
#include <DHT.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <math.h>
#include <Preferences.h>

// ==========================================================
// WIFI / FASTAPI
// ==========================================================

const char* WIFI_SSID     = "realme";
const char* WIFI_PASSWORD = "anbc8928";

const char* SERVER_HOST = "10.176.218.40";   // Change if laptop IP changes
const uint16_t SERVER_PORT = 8000;

String SERVER =
    String("http://") + SERVER_HOST + ":" + String(SERVER_PORT) + "/ingest";

String COW_SERVER =
    String("http://") + SERVER_HOST + ":" + String(SERVER_PORT) + "/cows";

// ==========================================================
// MAIN ESP32 PINOUT
// ==========================================================

#define DHTPIN       16
#define DHTTYPE      DHT22

#define TDS_PIN      34
#define MILK_ONEWIRE 4

#define BUTTON_PIN   27

// RC522 RFID reader on MAIN ESP32
#define RFID_SS_PIN   5
#define RFID_RST_PIN  26
#define RFID_SCK_PIN  18
#define RFID_MISO_PIN 19
#define RFID_MOSI_PIN 23

// ==========================================================
// SENSOR OBJECTS
// ==========================================================

DHT dht(DHTPIN, DHTTYPE);
OneWire milkOneWire(MILK_ONEWIRE);
DallasTemperature milkDS18B20(&milkOneWire);

MFRC522 rfid(RFID_SS_PIN, RFID_RST_PIN);

// ==========================================================
// AUTOMATIC RFID -> COW ID REGISTRY
// ==========================================================
// Every new RFID tag is automatically assigned COW400, COW401,
// COW402, ... The mapping is stored in ESP32 NVS and survives
// reset/power-off. Scanning the same RFID later returns the same ID.

Preferences rfidPrefs;
const uint16_t FIRST_AUTO_COW_NUMBER = 400;
const uint16_t MAX_RFID_RECORDS = 100;
unsigned long lastRfidTime = 0;
const unsigned long RFID_REPEAT_BLOCK_MS = 3000;

// ==========================================================
// TDS / MILK EC
// ==========================================================

#define VREF             3.3
#define ADC_MAX          4095.0
#define NUM_TDS_READINGS 20

// Keep the same provisional calibration as the original code.
#define CAL_SLOPE  3.58
#define CAL_OFFSET 0.0

#define TEMP_COEFF 0.02
#define TEMP_REF   25.0

#define MILK_TEMP_MIN 20.0
#define MILK_TEMP_MAX 45.0
#define COND_MIN      0.010
#define COND_MAX      30.0
#define YIELD_MAX     100.0

// ==========================================================
// ESP-NOW
// ==========================================================

// Replace with the actual MAC address printed by the neckband.
uint8_t NECKBAND_MAC[] = {
    0x88, 0x57, 0x21, 0x78, 0x91, 0x88
};

#define ESP_NOW_TIMEOUT_MS 12000

struct NeckbandMessage {
    char command[12];       // "MEASURED"
    char cow_id[32];
    float body_temperature;
    float activity_score;
    uint32_t sequence;
};

struct MainRequest {
    char command[12];       // "REQUEST"
    char cow_id[32];
    uint32_t sequence;
};

volatile bool neckbandDataReady = false;
NeckbandMessage latestNeckbandData;

uint32_t requestSequence = 0;

// ==========================================================
// COW STATE
// ==========================================================

String currentCowID = "";
String currentRFID = "";
int currentParity = 1;
bool cowRegistered = false;

// ==========================================================
// DEMO DATE
// ==========================================================

const int START_YEAR  = 2026;
const int START_MONTH = 9;
const int START_DAY   = 1;

const int DEMO_HOUR   = 10;
const int DEMO_MINUTE = 0;

int demoDay = 1;

// ==========================================================
// BUTTON
// ==========================================================

bool lastButtonState = HIGH;
unsigned long lastButtonTime = 0;
const unsigned long BUTTON_DEBOUNCE = 500;

// ==========================================================
// FORWARD DECLARATIONS
// ==========================================================

void connectWiFi();
void setupEspNow();
bool addNeckbandPeer();
void sendMeasurementRequest();
bool waitForNeckbandData(uint32_t expectedSequence);
void scanRFID();
String uidToString(MFRC522::Uid* uid);
bool registerCowOnServer(String cowId, int parity);
String readSerialLine();
void checkSerialCommands();
void takeMeasurement();
float readTDSAverage();
float calculateTDS(float voltage, float temperature);
float calculateMilkEC(float voltage, float temperature);
String getDemoDate();
bool postReadingToServer(const String& body);
void printNetworkInfo();

// ==========================================================
// ESP-NOW RECEIVE CALLBACK
// ==========================================================

void onEspNowReceive(
    const esp_now_recv_info_t *info,
    const uint8_t *data,
    int len
) {
    if (len != sizeof(NeckbandMessage)) {
        return;
    }

    NeckbandMessage msg;
    memcpy(&msg, data, sizeof(msg));

    msg.cow_id[sizeof(msg.cow_id) - 1] = '\0';
    msg.command[sizeof(msg.command) - 1] = '\0';
    msg.cow_id[sizeof(msg.cow_id) - 1] = '\0';

    if (strcmp(msg.command, "MEASURED") == 0) {
        latestNeckbandData = msg;
        neckbandDataReady = true;
    }
}

// ==========================================================
// SETUP
// ==========================================================

void setup() {
    Serial.begin(115200);
    delay(1000);

    // Persistent RFID -> COW400+ registry.
    rfidPrefs.begin("rfidmap", false);
    if (!rfidPrefs.isKey("next")) {
        rfidPrefs.putUShort("next", FIRST_AUTO_COW_NUMBER);
    }

    analogReadResolution(12);
    analogSetPinAttenuation(TDS_PIN, ADC_11db);

    pinMode(BUTTON_PIN, INPUT_PULLUP);

    dht.begin();
    milkDS18B20.begin();

    // RFID is connected to the MAIN ESP32.
    SPI.begin(RFID_SCK_PIN, RFID_MISO_PIN, RFID_MOSI_PIN, RFID_SS_PIN);
    rfid.PCD_Init();
    delay(50);

    // Wi-Fi must be STA mode before ESP-NOW.
    WiFi.mode(WIFI_STA);
    connectWiFi();

    setupEspNow();

    printNetworkInfo();

    Serial.println();
    Serial.println("========================================");
    Serial.println("       MASTISENSE MAIN ESP32");
    Serial.println("========================================");
    Serial.println("Wireless link : ESP-NOW");
    Serial.println("Gateway link  : Wi-Fi -> FastAPI");
    Serial.println("DHT22         : Farm temperature/humidity");
    Serial.println("DS18B20       : Milk temperature");
    Serial.println("TDS/EC        : Milk electrical response");
    Serial.println("Button        : Start measurement");
    Serial.println("========================================");
    Serial.println();
    Serial.println("RFID reader     : MAIN ESP32");
    Serial.println("Waiting for RFID tag on MAIN ESP32...");
    Serial.println("New RFID tags are automatically assigned COW400, COW401, ...");
}

// ==========================================================
// LOOP
// ==========================================================

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
        setupEspNow();
    }

    // RFID is read directly by the MAIN ESP32.
    scanRFID();

    checkSerialCommands();

    bool buttonState = digitalRead(BUTTON_PIN);

    if (buttonState == LOW &&
        lastButtonState == HIGH &&
        millis() - lastButtonTime > BUTTON_DEBOUNCE) {

        lastButtonTime = millis();

        if (!cowRegistered) {
            Serial.println();
            Serial.println("No cow selected.");
            Serial.println("Scan an RFID tag first.");
        }
        else {
            takeMeasurement();
        }
    }

    lastButtonState = buttonState;

    delay(20);
}

// ==========================================================
// WIFI
// ==========================================================

void connectWiFi() {
    Serial.println();
    Serial.println("Connecting to Wi-Fi...");

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;

    while (WiFi.status() != WL_CONNECTED && attempts < 40) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Wi-Fi connected.");
        Serial.print("Main ESP32 IP : ");
        Serial.println(WiFi.localIP());
        Serial.print("Wi-Fi channel : ");
        Serial.println(WiFi.channel());
        Serial.print("Main MAC      : ");
        Serial.println(WiFi.macAddress());
        Serial.print("FastAPI       : ");
        Serial.println(SERVER);
    }
    else {
        Serial.println("Wi-Fi connection FAILED.");
    }
}

// ==========================================================
// ESP-NOW SETUP
// ==========================================================

void setupEspNow() {
    if (esp_now_init() != ESP_OK) {
        Serial.println("ERROR: ESP-NOW initialization failed.");
        return;
    }

    esp_now_register_recv_cb(onEspNowReceive);

    addNeckbandPeer();
}

bool addNeckbandPeer() {
    if (esp_now_is_peer_exist(NECKBAND_MAC)) {
        return true;
    }

    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, NECKBAND_MAC, 6);
    peerInfo.channel = WiFi.channel();
    peerInfo.encrypt = false;

    esp_err_t result = esp_now_add_peer(&peerInfo);

    if (result == ESP_OK) {
        Serial.print("Neckband peer added. Channel: ");
        Serial.println(WiFi.channel());
        return true;
    }

    Serial.print("ERROR adding neckband peer: ");
    Serial.println(result);
    return false;
}

// ==========================================================
// SEND REQUEST TO NECKBAND
// ==========================================================

void sendMeasurementRequest() {
    MainRequest request = {};
    strncpy(request.command, "REQUEST", sizeof(request.command) - 1);
    strncpy(request.cow_id, currentCowID.c_str(), sizeof(request.cow_id) - 1);

    requestSequence++;
    request.sequence = requestSequence;

    neckbandDataReady = false;

    esp_err_t result = esp_now_send(
        NECKBAND_MAC,
        (uint8_t*)&request,
        sizeof(request)
    );

    Serial.println();
    Serial.println("Requesting neckband data...");

    if (result == ESP_OK) {
        Serial.print("Request sequence: ");
        Serial.println(request.sequence);
    }
    else {
        Serial.print("ESP-NOW send failed: ");
        Serial.println(result);
    }
}

// ==========================================================
// WAIT FOR NECKBAND DATA
// ==========================================================

bool waitForNeckbandData(uint32_t expectedSequence) {
    unsigned long start = millis();

    while (millis() - start < ESP_NOW_TIMEOUT_MS) {
        if (neckbandDataReady) {
            noInterrupts();
            NeckbandMessage msg = latestNeckbandData;
            neckbandDataReady = false;
            interrupts();

            if (msg.sequence == expectedSequence &&
                strcmp(msg.command, "MEASURED") == 0) {

                latestNeckbandData = msg;

                Serial.println();
                Serial.println("Neckband measurement received.");
                Serial.print("Cow ID          : ");
                Serial.println(msg.cow_id);
                Serial.print("Body temperature: ");
                Serial.print(msg.body_temperature, 2);
                Serial.println(" C");
                Serial.print("Activity score  : ");
                Serial.println(msg.activity_score, 3);

                return true;
            }
        }

        delay(10);
    }

    Serial.println();
    Serial.println("ERROR: Neckband response timeout.");
    Serial.println("Check:");
    Serial.println("1. Neckband is powered.");
    Serial.println("2. Both ESP32s are on the same Wi-Fi channel.");
    Serial.println("3. Neckband MAC is correct.");
    Serial.println("4. Neckband is within wireless range.");

    return false;
}

// ==========================================================
// RFID ON MAIN ESP32
// ==========================================================

// ==========================================================
// AUTOMATIC RFID -> COW ID REGISTRY
// ==========================================================
// Every new RFID tag is automatically assigned: COW400, COW401,
// COW402, ... The mapping is stored in ESP32 NVS, so it survives
// reset/power-off. Scanning the same RFID later returns the same ID.



String uidToString(MFRC522::Uid* uid) {
    String result = "";
    for (byte i = 0; i < uid->size; i++) {
        if (i > 0) result += " ";
        if (uid->uidByte[i] < 0x10) result += "0";
        result += String(uid->uidByte[i], HEX);
    }
    result.toUpperCase();
    return result;
}

String findStoredCowID(const String& uid) {
    uint16_t count = rfidPrefs.getUShort("count", 0);

    for (uint16_t i = 0; i < count && i < MAX_RFID_RECORDS; i++) {
        String uidKey = "uid" + String(i);
        String cowKey = "cow" + String(i);

        String storedUID = rfidPrefs.getString(uidKey.c_str(), "");
        storedUID.toUpperCase();

        if (storedUID == uid) {
            return rfidPrefs.getString(cowKey.c_str(), "");
        }
    }

    return "";
}

String getOrCreateCowID(const String& uid) {
    // First check whether this RFID was already assigned.
    String existingCowID = findStoredCowID(uid);
    if (existingCowID.length() > 0) {
        return existingCowID;
    }

    uint16_t count = rfidPrefs.getUShort("count", 0);

    if (count >= MAX_RFID_RECORDS) {
        Serial.println("ERROR: RFID registry is full.");
        return "";
    }

    uint16_t nextNumber = rfidPrefs.getUShort("next", FIRST_AUTO_COW_NUMBER);

    String newCowID = "COW" + String(nextNumber);

    String uidKey = "uid" + String(count);
    String cowKey = "cow" + String(count);

    rfidPrefs.putString(uidKey.c_str(), uid);
    rfidPrefs.putString(cowKey.c_str(), newCowID);
    rfidPrefs.putUShort("count", count + 1);
    rfidPrefs.putUShort("next", nextNumber + 1);

    Serial.println();
    Serial.println("NEW RFID REGISTERED");
    Serial.print("RFID UID : ");
    Serial.println(uid);
    Serial.print("Assigned : ");
    Serial.println(newCowID);

    return newCowID;
}

void scanRFID() {
    if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
        return;
    }

    String uid = uidToString(&rfid.uid);

    if (millis() - lastRfidTime > RFID_REPEAT_BLOCK_MS) {
        lastRfidTime = millis();

        // Automatically find or create the cow ID.
        // Existing RFID -> existing COW ID; new RFID -> COW400, COW401, ...
        String cowId = getOrCreateCowID(uid);

        if (cowId.length() == 0) {
            Serial.println("RFID registration failed. No cow selected.");
            rfid.PICC_HaltA();
            rfid.PCD_StopCrypto1();
            return;
        }

        // Prototype default. Change later if parity is captured separately.
        int parity = 1;

        currentRFID = uid;
        currentCowID = cowId;
        currentParity = parity;

        Serial.println();
        Serial.println("========================================");
        Serial.println("             RFID DETECTED");
        Serial.println("========================================");
        Serial.print("RFID UID : ");
        Serial.println(uid);
        Serial.print("Cow ID   : ");
        Serial.println(cowId);
        Serial.print("Parity   : ");
        Serial.println(parity);
        Serial.println("========================================");

        if (registerCowOnServer(cowId, parity)) {
            cowRegistered = true;
            demoDay = 1;
            Serial.println("Cow is ready.");
            Serial.println("Press the MAIN ESP32 button to measure.");
        } else {
            Serial.println("Cow registration failed.");
            cowRegistered = false;
        }
    }

    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
}

// ==========================================================
// REGISTER COW
// ==========================================================

bool registerCowOnServer(String cowId, int parity) {
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    WiFiClient client;
    HTTPClient http;

    String body = "{";
    body += "\"cow_id\":\"" + cowId + "\",";
    body += "\"parity\":" + String(parity);
    body += "}";

    Serial.print("Registering cow: ");
    Serial.println(cowId);

    http.begin(client, COW_SERVER);
    http.setTimeout(15000);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Accept", "application/json");

    int code = http.POST(body);
    String response = http.getString();

    Serial.print("POST /cows -> HTTP ");
    Serial.println(code);

    if (response.length() > 0) {
        Serial.println(response);
    }

    http.end();

    // 2xx = newly created/accepted.
    // 409 is treated as already registered.
    if ((code >= 200 && code < 300) || code == 409) {
        return true;
    }

    return false;
}

// ==========================================================
// MANUAL INPUT
// ==========================================================

String readSerialLine() {
    while (Serial.available() == 0) {
        delay(10);
    }

    String s = Serial.readStringUntil('\n');
    s.trim();
    return s;
}

// ==========================================================
// TDS
// ==========================================================

float readTDSAverage() {
    float total = 0;

    Serial.println();
    Serial.println("Taking 20 conductivity readings...");

    for (int i = 0; i < NUM_TDS_READINGS; i++) {
        int adcValue = analogRead(TDS_PIN);
        total += adcValue;

        Serial.print("Reading ");
        Serial.print(i + 1);
        Serial.print(" : ");
        Serial.println(adcValue);

        delay(50);
    }

    return total / NUM_TDS_READINGS;
}

float calculateTDS(float voltage, float temperature) {
    float compensationCoefficient =
        1.0 + TEMP_COEFF * (temperature - TEMP_REF);

    float compensatedVoltage =
        voltage / compensationCoefficient;

    float tds =
        (133.42 * compensatedVoltage * compensatedVoltage * compensatedVoltage)
        - (255.86 * compensatedVoltage * compensatedVoltage)
        + (857.39 * compensatedVoltage);

    if (tds < 0) {
        tds = 0;
    }

    return tds;
}

float calculateMilkEC(float voltage, float temperature) {
    float rawEC =
        CAL_SLOPE * voltage + CAL_OFFSET;

    float compensationCoefficient =
        1.0 + TEMP_COEFF * (temperature - TEMP_REF);

    float compensatedEC =
        rawEC / compensationCoefficient;

    if (compensatedEC < 0) {
        compensatedEC = 0;
    }

    return compensatedEC;
}

// ==========================================================
// DEMO DATE
// ==========================================================

String getDemoDate() {
    const int daysInMonth[13] = {
        0, 31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    };

    int year = START_YEAR;
    int month = START_MONTH;
    int day = START_DAY + demoDay - 1;

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
        year,
        month,
        day,
        DEMO_HOUR,
        DEMO_MINUTE
    );

    return String(buf);
}

// ==========================================================
// COMPLETE MEASUREMENT
// ==========================================================

void takeMeasurement() {
    Serial.println();
    Serial.println("========================================");
    Serial.println("       MEASUREMENT STARTED");
    Serial.println("========================================");
    Serial.print("Cow ID: ");
    Serial.println(currentCowID);

    // ======================================================
    // STEP 1: BUTTON -> REQUEST NECKBAND MEASUREMENT
    // ======================================================
    // The button press immediately requests the two
    // neckband measurements: body temperature + activity.

    sendMeasurementRequest();

    uint32_t expectedSequence = requestSequence;

    if (!waitForNeckbandData(expectedSequence)) {
        Serial.println("Measurement cancelled.");
        Serial.println("Demo day NOT advanced.");
        return;
    }

    NeckbandMessage neck = latestNeckbandData;

    float bodyTemperature = neck.body_temperature;
    float activityScore = neck.activity_score;

    // ======================================================
    // STEP 2: MAIN ESP32 MEASUREMENTS / INPUTS
    // ======================================================

    Serial.println();
    Serial.println("========================================");
    Serial.println(" NECKBAND DATA RECEIVED - MAIN MEASUREMENTS");
    Serial.println("========================================");

    // ------------------------------------------------------
    // MILK YIELD
    // ------------------------------------------------------

    Serial.println();
    Serial.println("Enter milk yield in litres.");
    Serial.println("Example: 17.0");

    String yieldInput = readSerialLine();
    float milkYield = yieldInput.toFloat();

    if (milkYield <= 0 || milkYield > YIELD_MAX) {
        Serial.println("Invalid milk yield. Measurement cancelled.");
        return;
    }

    // ------------------------------------------------------
    // SCC
    // ------------------------------------------------------

    Serial.println();
    Serial.println("Enter SCC in cells/mL.");
    Serial.println("Example: 250000");
    Serial.println("Press ENTER alone to skip.");

    String sccInput = readSerialLine();

    bool hasSCC = sccInput.length() > 0;
    float sccValue = 0;

    if (hasSCC) {
        sccValue = sccInput.toFloat();

        if (sccValue < 0 || sccValue > 20000000.0) {
            Serial.println("Invalid SCC. SCC will be omitted.");
            hasSCC = false;
        }
    }

    // ------------------------------------------------------
    // DHT22 - FARM ENVIRONMENT
    // ------------------------------------------------------

    float farmTemperature = dht.readTemperature();
    float farmHumidity = dht.readHumidity();

    bool hasFarmEnv = true;

    if (isnan(farmTemperature) || isnan(farmHumidity)) {
        Serial.println("WARNING: DHT22 read failed.");
        hasFarmEnv = false;
    }

    // ------------------------------------------------------
    // MAIN DS18B20 - MILK TEMPERATURE
    // ------------------------------------------------------

    milkDS18B20.requestTemperatures();

    float milkTemperature =
        milkDS18B20.getTempCByIndex(0);

    if (milkTemperature == DEVICE_DISCONNECTED_C) {
        Serial.println("ERROR: Milk DS18B20 read failed.");
        Serial.println("Measurement aborted.");
        return;
    }

    if (milkTemperature < MILK_TEMP_MIN ||
        milkTemperature > MILK_TEMP_MAX) {

        Serial.print("Milk temperature out of range: ");
        Serial.print(milkTemperature, 2);
        Serial.println(" C");
        Serial.println("Measurement aborted.");
        return;
    }

    // ------------------------------------------------------
    // MAIN CONDUCTIVITY SENSOR
    // ------------------------------------------------------

    float averageADC = readTDSAverage();

    float milkVoltage =
        (averageADC / ADC_MAX) * VREF;

    float tds =
        calculateTDS(milkVoltage, milkTemperature);

    float conductivity =
        calculateMilkEC(milkVoltage, milkTemperature);

    if (conductivity < COND_MIN) {
        conductivity = COND_MIN;
    }

    if (conductivity > COND_MAX) {
        conductivity = COND_MAX;
    }

    // ------------------------------------------------------
    // DEMO DATE
    // ------------------------------------------------------

    String timestamp = getDemoDate();

    // ======================================================
    // STEP 3: SHOW COMPLETE MEASUREMENT
    // ======================================================

    Serial.println();
    Serial.println("========================================");
    Serial.println("       COMPLETE SENSOR VALUES");
    Serial.println("========================================");

    Serial.print("Cow ID             : ");
    Serial.println(currentCowID);

    Serial.print("RFID UID           : ");
    Serial.println(currentRFID);

    Serial.print("Demo Day           : ");
    Serial.println(demoDay);

    Serial.print("Timestamp          : ");
    Serial.println(timestamp);

    Serial.print("Milk Yield         : ");
    Serial.print(milkYield, 2);
    Serial.println(" L");

    if (hasSCC) {
        Serial.print("SCC                : ");
        Serial.print(sccValue, 0);
        Serial.println(" cells/mL");
    }
    else {
        Serial.println("SCC                : not measured");
    }

    if (hasFarmEnv) {
        Serial.print("Farm Temperature   : ");
        Serial.print(farmTemperature, 2);
        Serial.println(" C");

        Serial.print("Farm Humidity      : ");
        Serial.print(farmHumidity, 2);
        Serial.println(" %");
    }
    else {
        Serial.println("Farm Temp/Humidity : omitted");
    }

    Serial.print("Milk Temperature   : ");
    Serial.print(milkTemperature, 2);
    Serial.println(" C");

    Serial.print("Body Temperature   : ");
    Serial.print(bodyTemperature, 2);
    Serial.println(" C");

    Serial.print("Activity Score     : ");
    Serial.println(activityScore, 3);

    Serial.print("Average ADC        : ");
    Serial.println(averageADC, 1);

    Serial.print("Sensor Voltage     : ");
    Serial.print(milkVoltage, 4);
    Serial.println(" V");

    Serial.print("Estimated TDS      : ");
    Serial.print(tds, 2);
    Serial.println(" ppm");

    Serial.print("Milk EC            : ");
    Serial.print(conductivity, 3);
    Serial.println(" mS/cm");

    // ======================================================
    // STEP 4: ONE COMPLETE JSON -> FASTAPI /INGEST
    // ======================================================

    String body = "{";

    body += "\"cow_id\":\"" + currentCowID + "\",";
    body += "\"timestamp\":\"" + timestamp + "\",";
    body += "\"milk_yield_l\":" + String(milkYield, 2) + ",";
    body += "\"milk_conductivity\":" + String(conductivity, 3) + ",";
    body += "\"milk_temp_c\":" + String(milkTemperature, 2) + ",";
    body += "\"activity_score\":" + String(activityScore, 3) + ",";
    body += "\"body_temperature\":" + String(bodyTemperature, 2);

    if (hasSCC) {
        body += ",\"scc_value\":" + String(sccValue, 0);
    }

    if (hasFarmEnv) {
        body += ",\"farm_temperature_c\":" +
                String(farmTemperature, 2);

        body += ",\"farm_humidity\":" +
                String(farmHumidity, 2);
    }

    body += ",\"source\":\"esp32\"";
    body += "}";

    Serial.println();
    Serial.println("========================================");
    Serial.println("             JSON TO SERVER");
    Serial.println("========================================");
    Serial.println(body);

    // ======================================================
    // STEP 5: SEND TO FASTAPI -> ML
    // ======================================================

    if (postReadingToServer(body)) {
        demoDay++;

        Serial.println();
        Serial.println("Sample accepted by FastAPI.");
        Serial.println("ML prediction pipeline triggered.");
        Serial.print("Next demo day: ");
        Serial.println(demoDay);
    }
    else {
        Serial.println();
        Serial.println("Sample was NOT accepted.");
        Serial.println("Demo day NOT advanced.");
    }
}

// ==========================================================
// POST /INGEST
// ==========================================================

bool postReadingToServer(const String& body) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Wi-Fi is not connected.");
        return false;
    }

    WiFiClient client;
    HTTPClient http;

    http.begin(client, SERVER);
    http.setConnectTimeout(5000);
    http.setTimeout(20000);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Accept", "application/json");

    Serial.print("POST ");
    Serial.println(SERVER);

    int code = http.POST(body);

    Serial.print("HTTP Response Code: ");
    Serial.println(code);

    String response = http.getString();

    if (response.length() > 0) {
        Serial.println();
        Serial.println("SERVER RESPONSE:");
        Serial.println(response);
    }

    http.end();

    return (code >= 200 && code < 300);
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

    if (command == "STATUS") {
        printNetworkInfo();
        Serial.print("Selected cow: ");
        Serial.println(currentCowID);
        Serial.print("RFID UID: ");
        Serial.println(currentRFID);
        return;
    }

    if (command == "RESETCOW") {
        currentCowID = "";
        currentRFID = "";
        cowRegistered = false;
        Serial.println("Cow selection cleared. Scan RFID again.");
        return;
    }

    if (command.length() > 0) {
        Serial.println("Commands: STATUS, RESETCOW");
    }
}

// ==========================================================
// NETWORK INFO
// ==========================================================

void printNetworkInfo() {
    Serial.println();
    Serial.println("---------- NETWORK INFO ----------");
    Serial.print("Main MAC      : ");
    Serial.println(WiFi.macAddress());
    Serial.print("IP            : ");
    Serial.println(WiFi.localIP());
    Serial.print("Wi-Fi channel : ");
    Serial.println(WiFi.channel());
    Serial.print("FastAPI       : ");
    Serial.println(SERVER);
    Serial.println("----------------------------------");
}
