// MastiSense NECKBAND ESP32
// Body temperature + ADXL345 activity
// Wireless communication to MAIN ESP32: ESP-NOW
//
// Data flow:
// Main ESP32 selects cow by RFID.
// DS18B20 -> body temperature
// ADXL345 -> activity score
// ESP-NOW -> Main ESP32
//
// IMPORTANT:
// 1) Fill WIFI_SSID / WIFI_PASSWORD.
// 2) Put the MAIN ESP32 MAC in MAIN_ESP32_MAC.
// 3) RFID is handled entirely by the MAIN ESP32.
// 4) ADXL345 activity analysis is kept from the uploaded program:
//    256 samples, 50 Hz, 5.12 s, FFT + RMS + rhythmicity.

#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <arduinoFFT.h>
#include <math.h>

// ==========================================================
// WIFI
// ==========================================================

const char* WIFI_SSID     = "realme";
const char* WIFI_PASSWORD = "anbc8928";

// ==========================================================
// MAIN ESP32 MAC
// ==========================================================
// Get this from the MAIN ESP32 Serial Monitor.
// Example: AA:BB:CC:DD:EE:FF

uint8_t MAIN_ESP32_MAC[] = {
    0x14, 0x2B, 0x2F, 0xDA, 0xDB, 0xF4
};

// ==========================================================
// PINOUT
// ==========================================================

// Body temperature DS18B20
#define BODY_TEMP_PIN 4

// ADXL345 I2C
#define SDA_PIN 21
#define SCL_PIN 22

// ==========================================================
// SENSOR OBJECTS
// ==========================================================

OneWire bodyOneWire(
    BODY_TEMP_PIN
);

DallasTemperature bodyDS18B20(
    &bodyOneWire
);

Adafruit_ADXL345_Unified accel =
    Adafruit_ADXL345_Unified(12345);

// ==========================================================
// ADXL345 ACTIVITY CONFIGURATION
// ==========================================================
// This is intentionally kept the same as the uploaded
// ADXL345 activity program.

#define NUM_ACTIVITY_SAMPLES 256
#define ACTIVITY_SAMPLE_RATE 50

#define NOISE_RMS_THRESHOLD 0.08
#define STATIONARY_RMS_THRESHOLD 0.20
#define REPETITIVE_RHYTHMICITY_THRESHOLD 0.05
#define FAST_SLOW_FREQUENCY_BOUNDARY 4.0

double activityRawData[
    NUM_ACTIVITY_SAMPLES
];

double activityVReal[
    NUM_ACTIVITY_SAMPLES
];

double activityVImag[
    NUM_ACTIVITY_SAMPLES
];

ArduinoFFT<double> activityFFT =
    ArduinoFFT<double>(
        activityVReal,
        activityVImag,
        NUM_ACTIVITY_SAMPLES,
        ACTIVITY_SAMPLE_RATE
    );

// ==========================================================
// ESP-NOW MESSAGES
// ==========================================================

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

volatile bool measurementRequested = false;
MainRequest pendingRequest;

// ==========================================================
// CURRENT REQUEST STATE
// ==========================================================

String currentCowID = "";

// ==========================================================
// ESP-NOW RECEIVE CALLBACK
// ==========================================================

void onEspNowReceive(
    const esp_now_recv_info_t *info,
    const uint8_t *data,
    int len
) {
    if (len != sizeof(MainRequest)) {
        return;
    }

    MainRequest request;
    memcpy(&request, data, sizeof(request));

    request.command[
        sizeof(request.command) - 1
    ] = '\0';

    request.cow_id[
        sizeof(request.cow_id) - 1
    ] = '\0';

    if (strcmp(request.command, "REQUEST") == 0) {
        pendingRequest = request;
        measurementRequested = true;
    }
}

// ==========================================================
// SETUP
// ==========================================================

void setup() {
    Serial.begin(115200);
    delay(1000);

    // ------------------------------------------------------
    // BODY TEMPERATURE
    // ------------------------------------------------------

    bodyDS18B20.begin();

    // ------------------------------------------------------
    // ADXL345
    // ------------------------------------------------------

    Wire.begin(
        SDA_PIN,
        SCL_PIN
    );

    Wire.setClock(100000);

    Serial.println();
    Serial.println("Initializing ADXL345...");

    if (!accel.begin(0x53)) {
        Serial.println("ERROR: ADXL345 NOT DETECTED.");
        Serial.println("Check SDA=21, SCL=22, VCC=3.3V, GND.");
        while (1) {
            delay(1000);
        }
    }

    accel.setRange(
        ADXL345_RANGE_4_G
    );

    Serial.println("ADXL345 detected.");
    Serial.println("Range: +/- 4G");

    // ------------------------------------------------------
    // WIFI
    // ------------------------------------------------------

    WiFi.mode(WIFI_STA);
    connectWiFi();

    // ------------------------------------------------------
    // ESP-NOW
    // ------------------------------------------------------

    setupEspNow();

    // ------------------------------------------------------
    // HEADER
    // ------------------------------------------------------

    Serial.println();
    Serial.println("========================================");
    Serial.println("       MASTISENSE NECKBAND ESP32");
    Serial.println("========================================");
    Serial.println("RFID      -> handled by MAIN ESP32");
    Serial.println("DS18B20   -> Body temperature");
    Serial.println("ADXL345   -> Cow activity");
    Serial.println("Wireless  -> ESP-NOW");
    Serial.println();
    Serial.println("Activity analysis:");
    Serial.println("Sampling rate : 50 Hz");
    Serial.println("Samples       : 256");
    Serial.println("Window        : 5.12 seconds");
    Serial.println("========================================");

    Serial.print("Neckband MAC : ");
    Serial.println(WiFi.macAddress());

    Serial.print("Wi-Fi channel: ");
    Serial.println(WiFi.channel());

    Serial.println();
    Serial.println("Waiting for measurement request from MAIN ESP32...");
}

// ==========================================================
// LOOP
// ==========================================================

void loop() {
    // RFID is handled by the MAIN ESP32.
    // This ESP32 waits only for the measurement request.

    // ------------------------------------------------------
    // MEASUREMENT REQUEST FROM MAIN
    // ------------------------------------------------------

    if (measurementRequested) {
        noInterrupts();
        MainRequest request = pendingRequest;
        measurementRequested = false;
        interrupts();

        String requestedCow =
            String(request.cow_id);

        // Main ESP32 already selected the cow using RFID.
        if (requestedCow.length() > 0) {
            currentCowID = requestedCow;
        }

        Serial.println();
        Serial.println("========================================");
        Serial.println("      MEASUREMENT REQUEST RECEIVED");
        Serial.println("========================================");
        Serial.print("Cow ID : ");
        Serial.println(currentCowID);
        Serial.print("Sequence : ");
        Serial.println(request.sequence);

        // --------------------------------------------------
        // BODY TEMPERATURE
        // --------------------------------------------------

        float bodyTemperature =
            readBodyTemperature();

        if (isnan(bodyTemperature)) {
    Serial.println(
        "Body temperature read failed."
    );
    Serial.println(
        "Measurement response NOT sent."
    );
    delay(20);
    return;
}

        // --------------------------------------------------
        // ACTIVITY
        // --------------------------------------------------

        float activityScore =
            measureActivityScore();

        // --------------------------------------------------
        // SEND TO MAIN
        // --------------------------------------------------

        sendMeasurementToMain(
            currentCowID,
            bodyTemperature,
            activityScore,
            request.sequence
        );

        Serial.println();
        Serial.println("Neckband measurement complete.");
        Serial.println("Waiting for next measurement request...");
    }

    delay(20);
}

// ==========================================================
// WIFI
// ==========================================================

void connectWiFi() {
    Serial.println();
    Serial.println("Connecting neckband to Wi-Fi...");

    WiFi.mode(WIFI_STA);
    WiFi.begin(
        WIFI_SSID,
        WIFI_PASSWORD
    );

    int attempts = 0;

    while (
        WiFi.status() != WL_CONNECTED &&
        attempts < 40
    ) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("Neckband Wi-Fi connected.");
        Serial.print("Neckband IP : ");
        Serial.println(WiFi.localIP());
        Serial.print("Channel     : ");
        Serial.println(WiFi.channel());
        Serial.print("MAC         : ");
        Serial.println(WiFi.macAddress());
    }
    else {
        Serial.println("Neckband Wi-Fi connection FAILED.");
    }
}

// ==========================================================
// ESP-NOW SETUP
// ==========================================================

void setupEspNow() {
    if (esp_now_init() != ESP_OK) {
        Serial.println(
            "ERROR: ESP-NOW initialization failed."
        );
        return;
    }

    esp_now_register_recv_cb(
        onEspNowReceive
    );

    addMainPeer();
}

bool addMainPeer() {
    if (esp_now_is_peer_exist(MAIN_ESP32_MAC)) {
        return true;
    }

    esp_now_peer_info_t peerInfo = {};

    memcpy(
        peerInfo.peer_addr,
        MAIN_ESP32_MAC,
        6
    );

    // Both ESP32s are connected to the same Wi-Fi AP,
    // so they are on the same channel.
    peerInfo.channel = WiFi.channel();
    peerInfo.encrypt = false;

    esp_err_t result =
        esp_now_add_peer(&peerInfo);

    if (result == ESP_OK) {
        Serial.print(
            "Main ESP32 peer added. Channel: "
        );
        Serial.println(
            WiFi.channel()
        );
        return true;
    }

    Serial.print(
        "ERROR adding Main ESP32 peer: "
    );
    Serial.println(result);

    return false;
}

// ==========================================================
// SEND SENSOR MEASUREMENT
// ==========================================================

void sendMeasurementToMain(
    const String& cowId,
    float bodyTemperature,
    float activityScore,
    uint32_t sequence
) {
    NeckbandMessage msg = {};

    strncpy(
        msg.command,
        "MEASURED",
        sizeof(msg.command) - 1
    );

    strncpy(
        msg.cow_id,
        cowId.c_str(),
        sizeof(msg.cow_id) - 1
    );

    msg.body_temperature = bodyTemperature;
    msg.activity_score = activityScore;
    msg.sequence = sequence;
    esp_err_t result =
        esp_now_send(
            MAIN_ESP32_MAC,
            (uint8_t*)&msg,
            sizeof(msg)
        );

    if (result == ESP_OK) {
        Serial.println(
            "Body temp + activity -> Main: sent."
        );
    }
    else {
        Serial.print(
            "Measurement ESP-NOW send failed: "
        );
        Serial.println(result);
    }
}

// ==========================================================
// BODY TEMPERATURE
// ==========================================================

float readBodyTemperature() {
    Serial.println();
    Serial.println(
        "Reading body temperature..."
    );

    bodyDS18B20.requestTemperatures();

    float temp =
        bodyDS18B20.getTempCByIndex(0);

    if (temp == DEVICE_DISCONNECTED_C) {
        Serial.println(
            "ERROR: Body DS18B20 disconnected."
        );
        return NAN;
    }

    Serial.print(
        "Body temperature: "
    );
    Serial.print(
        temp,
        2
    );
    Serial.println(
        " C"
    );

    return temp;
}

// ==========================================================
// ADXL345 ACCELERATION MAGNITUDE
// ==========================================================

double readAccelerationMagnitude() {
    sensors_event_t event;

    accel.getEvent(
        &event
    );

    double X =
        event.acceleration.x;

    double Y =
        event.acceleration.y;

    double Z =
        event.acceleration.z;

    return sqrt(
        X * X +
        Y * Y +
        Z * Z
    );
}

// ==========================================================
// ACTIVITY MEASUREMENT
// ==========================================================
// EXACT ANALYSIS STRUCTURE FROM THE UPLOADED PROGRAM:
//
// 256 samples
// 50 Hz
// 5.12 seconds
// mean removal
// RMS
// peak-to-peak
// Hamming window
// FFT
// dominant frequency
// rhythmicity
// classification
// activity score
//
// 0.10 -> stationary
// 0.35 -> little repetitive
// 0.60 -> slow repetitive
// 0.80 -> fast repetitive
// 1.00 -> random movement
// ==========================================================

float measureActivityScore() {
    Serial.println();
    Serial.println(
        "========================================"
    );
    Serial.println(
        "       MEASURING COW ACTIVITY"
    );
    Serial.println(
        "========================================"
    );

    Serial.println(
        "Collecting ADXL345 data..."
    );

    Serial.println(
        "Duration: approximately 5.12 seconds"
    );

    // ------------------------------------------------------
    // COLLECT 256 SAMPLES AT 50 Hz
    // ------------------------------------------------------

    unsigned long nextTime =
        micros();

    for (
        int i = 0;
        i < NUM_ACTIVITY_SAMPLES;
        i++
    ) {
        activityRawData[i] =
            readAccelerationMagnitude();

        nextTime +=
            1000000UL /
            ACTIVITY_SAMPLE_RATE;

        while (
            (long)(
                micros() -
                nextTime
            ) < 0
        ) {
        }
    }

    // ------------------------------------------------------
    // COPY TO FFT ARRAYS
    // ------------------------------------------------------

    for (
        int i = 0;
        i < NUM_ACTIVITY_SAMPLES;
        i++
    ) {
        activityVReal[i] =
            activityRawData[i];

        activityVImag[i] = 0;
    }

    // ------------------------------------------------------
    // MEAN
    // ------------------------------------------------------

    double mean = 0;

    for (
        int i = 0;
        i < NUM_ACTIVITY_SAMPLES;
        i++
    ) {
        mean +=
            activityVReal[i];
    }

    mean /=
        NUM_ACTIVITY_SAMPLES;

    // ------------------------------------------------------
    // REMOVE DC / GRAVITY COMPONENT
    // ------------------------------------------------------

    double sumSquared = 0;

    double minimum =
        999999;

    double maximum =
        -999999;

    for (
        int i = 0;
        i < NUM_ACTIVITY_SAMPLES;
        i++
    ) {
        double x =
            activityVReal[i] -
            mean;

        activityVReal[i] =
            x;

        sumSquared +=
            x * x;

        if (x < minimum) {
            minimum = x;
        }

        if (x > maximum) {
            maximum = x;
        }
    }

    // ------------------------------------------------------
    // RMS
    // ------------------------------------------------------

    double RMS =
        sqrt(
            sumSquared /
            NUM_ACTIVITY_SAMPLES
        );

    // ------------------------------------------------------
    // PEAK TO PEAK
    // ------------------------------------------------------

    double peakToPeak =
        maximum -
        minimum;

    // ------------------------------------------------------
    // HAMMING WINDOW
    // ------------------------------------------------------

    activityFFT.windowing(
        FFTWindow::Hamming,
        FFTDirection::Forward
    );

    // ------------------------------------------------------
    // FFT
    // ------------------------------------------------------

    activityFFT.compute(
        FFTDirection::Forward
    );

    // ------------------------------------------------------
    // MAGNITUDE
    // ------------------------------------------------------

    activityFFT.complexToMagnitude();

    // ------------------------------------------------------
    // DOMINANT FREQUENCY
    // ------------------------------------------------------

    double maximumMagnitude = 0;
    double dominantFrequency = 0;
    double totalPower = 0;

    for (
        int i = 1;
        i < NUM_ACTIVITY_SAMPLES / 2;
        i++
    ) {
        double frequency =
            (
                (double)i *
                ACTIVITY_SAMPLE_RATE
            )
            /
            NUM_ACTIVITY_SAMPLES;

        double magnitude =
            activityVReal[i];

        double power =
            magnitude *
            magnitude;

        totalPower +=
            power;

        if (
            magnitude >
            maximumMagnitude
        ) {
            maximumMagnitude =
                magnitude;

            dominantFrequency =
                frequency;
        }
    }

    // ------------------------------------------------------
    // RHYTHMICITY
    // ------------------------------------------------------

    double peakPower =
        maximumMagnitude *
        maximumMagnitude;

    double rhythmicity = 0;

    if (totalPower > 0) {
        rhythmicity =
            peakPower /
            totalPower;
    }

    // ------------------------------------------------------
    // CLASSIFICATION
    // ------------------------------------------------------

    String classification;

    if (
        RMS <
        NOISE_RMS_THRESHOLD
    ) {
        classification =
            "STATIONARY";
    }
    else if (
        RMS <
        STATIONARY_RMS_THRESHOLD
    ) {
        if (
            rhythmicity >=
            REPETITIVE_RHYTHMICITY_THRESHOLD
        ) {
            classification =
                "LITTLE REPETITIVE";
        }
        else {
            classification =
                "STATIONARY";
        }
    }
    else {
        if (
            rhythmicity >=
            REPETITIVE_RHYTHMICITY_THRESHOLD
        ) {
            if (
                dominantFrequency >=
                FAST_SLOW_FREQUENCY_BOUNDARY
            ) {
                classification =
                    "FAST REPETITIVE";
            }
            else {
                classification =
                    "SLOW REPETITIVE";
            }
        }
        else {
            classification =
                "RANDOM MOVEMENT";
        }
    }

    // ------------------------------------------------------
    // CLASSIFICATION -> SCORE
    // ------------------------------------------------------

    float activityScore = 0.0;

    if (
        classification ==
        "STATIONARY"
    ) {
        activityScore =
            0.10;
    }
    else if (
        classification ==
        "LITTLE REPETITIVE"
    ) {
        activityScore =
            0.35;
    }
    else if (
        classification ==
        "SLOW REPETITIVE"
    ) {
        activityScore =
            0.60;
    }
    else if (
        classification ==
        "FAST REPETITIVE"
    ) {
        activityScore =
            0.80;
    }
    else if (
        classification ==
        "RANDOM MOVEMENT"
    ) {
        activityScore =
            1.00;
    }

    // ------------------------------------------------------
    // SERIAL RESULT
    // ------------------------------------------------------

    Serial.println();
    Serial.println(
        "----------------------------------------"
    );

    Serial.println(
        "       ADXL345 ACTIVITY RESULT"
    );

    Serial.println(
        "----------------------------------------"
    );

    Serial.print(
        "RMS                : "
    );

    Serial.println(
        RMS,
        3
    );

    Serial.print(
        "Peak-to-Peak       : "
    );

    Serial.println(
        peakToPeak,
        3
    );

    Serial.print(
        "Dominant Frequency : "
    );

    Serial.print(
        dominantFrequency,
        3
    );

    Serial.println(
        " Hz"
    );

    Serial.print(
        "Rhythmicity        : "
    );

    Serial.println(
        rhythmicity,
        3
    );

    Serial.print(
        "Movement Type      : "
    );

    Serial.println(
        classification
    );

    Serial.print(
        "Activity Score     : "
    );

    Serial.println(
        activityScore,
        3
    );

    Serial.println(
        "----------------------------------------"
    );

    return activityScore;
}