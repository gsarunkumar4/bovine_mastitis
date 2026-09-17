// ==========================================================
// secrets_example.h  —  TEMPLATE (safe to commit)
// ==========================================================
//
// SETUP:
//   1. Copy this file and rename the copy to  secrets.h
//   2. Fill in your real values in secrets.h
//   3. NEVER commit secrets.h — it is in .gitignore
//
// The .ino includes "secrets.h", not this file.
// ==========================================================

#ifndef SECRETS_H
#define SECRETS_H

// ----------------------------------------------------------
// Blynk  (https://blynk.cloud → Device → Device Info)
// ----------------------------------------------------------

#define BLYNK_TEMPLATE_ID   "YOUR_TEMPLATE_ID"
#define BLYNK_TEMPLATE_NAME "YOUR_TEMPLATE_NAME"
#define BLYNK_AUTH_TOKEN    "YOUR_BLYNK_AUTH_TOKEN"

// ----------------------------------------------------------
// WiFi  (use your phone hotspot for field demos)
// ----------------------------------------------------------

#define WIFI_SSID_VALUE     "YOUR_WIFI_SSID"
#define WIFI_PASSWORD_VALUE "YOUR_WIFI_PASSWORD"

// ----------------------------------------------------------
// Backend server
// ----------------------------------------------------------
// Your laptop's IPv4 address on the same network as the ESP32.
//   Windows : ipconfig      → "IPv4 Address"
//   Mac      : ifconfig en0  → "inet"
//   Linux    : hostname -I
//
// This changes whenever you reconnect to a different network,
// so re-check it before every demo.

#define SERVER_HOST "192.168.1.100"
#define SERVER_PORT "8000"

#endif  // SECRETS_H