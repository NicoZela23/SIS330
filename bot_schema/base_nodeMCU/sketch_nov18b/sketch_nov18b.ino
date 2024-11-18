#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>
#define controlPin 12

const char* ssid = "xzt";
const char* password = "#10315168#";
const int port = 80;

ESP8266WebServer server(port);
volatile bool pumpActive = false;

void setup() {
    Serial.begin(115200);
    pinMode(controlPin, OUTPUT);
    digitalWrite(controlPin, LOW);
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    server.on("/servo/command", HTTP_POST, handlePumpControl);
    server.begin();
}

void handlePumpControl() {
    if (pumpActive) {
        server.send(409, "application/json", "{\"error\":\"Pump already active\"}");
        return;
    }

    if (server.hasArg("plain")) {
        String body = server.arg("plain");
        StaticJsonDocument<200> doc;
        DeserializationError error = deserializeJson(doc, body);
        
        if (!error) {
            int duration = doc["angle"].as<int>();
            if (duration >= 1000 && duration <= 10000) {
                pumpActive = true;
                digitalWrite(controlPin, HIGH);
                Serial.println("Pump ON for " + String(duration) + "ms");
                server.send(200, "application/json", "{\"status\":\"success\",\"duration\":" + String(duration) + "}");
                delay(duration);
                digitalWrite(controlPin, LOW);
                pumpActive = false;
                Serial.println("Pump OFF");
                return;
            }
        }
    }
    server.send(400, "application/json", "{\"error\":\"Invalid request\"}");
}

void loop() {
    server.handleClient();
    yield();
}