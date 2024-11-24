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

// Add these variables for non-blocking control
unsigned long pumpOneEndTime = 0;
unsigned long pumpTwoEndTime = 0;
bool pumpOneRunning = false;
bool pumpTwoRunning = false;

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
            
            Serial.println("\nReceived pump durations:");
            Serial.print("Pump 1 duration: ");
            Serial.println(durationPump1);
            Serial.print("Pump 2 duration: ");
            Serial.println(durationPump2);
            
            if (durationPump1 >= 1000 && durationPump1 <= 10000 && 
                durationPump2 >= 1000 && durationPump2 <= 10000) {
                
                unsigned long currentTime = millis();
                pumpOneEndTime = currentTime + durationPump1;
                pumpTwoEndTime = currentTime + durationPump2;
                
                digitalWrite(pumpOnePin, HIGH);
                digitalWrite(pumpTwoPin, HIGH);
                pumpOneRunning = true;
                pumpTwoRunning = true;
                pumpActive = true;
                
                server.send(200, "application/json", "{\"status\":\"success\",\"pump1_duration\":" + String(durationPump1) + ",\"pump2_duration\":" + String(durationPump2) + "}");
                return;
            }
        }
    }
    server.send(400, "application/json", "{\"error\":\"Invalid request\"}");
}

void checkPumps() {
    if (!pumpActive) return;
    
    unsigned long currentTime = millis();
    
    if (pumpOneRunning && currentTime >= pumpOneEndTime) {
        digitalWrite(pumpOnePin, LOW);
        pumpOneRunning = false;
        Serial.println("Pump 1 stopped");
    }
    
    if (pumpTwoRunning && currentTime >= pumpTwoEndTime) {
        digitalWrite(pumpTwoPin, LOW);
        pumpTwoRunning = false;
        Serial.println("Pump 2 stopped");
    }
    
    // Reset pumpActive when both pumps are done
    if (!pumpOneRunning && !pumpTwoRunning) {
        pumpActive = false;
        Serial.println("All pumps stopped");
    }
}

void loop() {
    server.handleClient();
    checkPumps();
    yield();
}