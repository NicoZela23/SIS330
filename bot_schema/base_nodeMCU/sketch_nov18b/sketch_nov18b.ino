#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>
#define pumpOnePin 12
#define pumpTwoPin 14

const char* ssid = "xzt";
const char* password = "#10315168#";
const int port = 80;

ESP8266WebServer server(port);
volatile bool pumpActive = false;

void setup() {
    Serial.begin(115200);
    pinMode(pumpOnePin, OUTPUT);
    pinMode(pumpTwoPin, OUTPUT);
    digitalWrite(pumpOnePin, LOW);
    digitalWrite(pumpTwoPin, LOW);
    
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nConnected to WiFi");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    server.on("/pump/action", HTTP_POST, handlePumpControl);
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
            int durationPump1 = doc["mix1"].as<int>();
            int durationPump2 = doc["mix2"].as<int>();
            
            if (durationPump1 >= 1000 && durationPump1 <= 10000 && 
                durationPump2 >= 1000 && durationPump2 <= 10000) {
                
                pumpActive = true;
                unsigned long startTime = millis();
                
                digitalWrite(pumpOnePin, HIGH);
                digitalWrite(pumpTwoPin, HIGH);
                
                while (millis() - startTime < max(durationPump1, durationPump2)) {
                    server.handleClient();
                    if (millis() - startTime >= durationPump1) {
                        digitalWrite(pumpOnePin, LOW);
                    }
                    if (millis() - startTime >= durationPump2) {
                        digitalWrite(pumpTwoPin, LOW);
                    }
                    yield();
                }
                
                pumpActive = false;
                server.send(200, "application/json", "{\"status\":\"success\",\"pump1_duration\":" + String(durationPump1) + ",\"pump2_duration\":" + String(durationPump2) + "}");
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