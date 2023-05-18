#include <WiFiNINA.h>
#include "arduino_secrets.h"


// Pins
#define TEMPERATURE_PIN A0

#define LED_PIN 2


// WiFi
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;

int status = WL_IDLE_STATUS;

WiFiServer server(80);      // port 80


// Temperature sensor
const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;
double v, r, temperature;


// Functions prototypes
void process(WiFiClient client);
void printResponse(WiFiClient client, int code, String body);
String senMlEncode(String dev, int val);


void setup() {
    Serial.begin(9600);

    while (status != WL_CONNECTED) {
        Serial.print("Attempting to connect to SSID: ");
        Serial.println(ssid);

        status = WiFi.begin(ssid, pass);
        delay(2000);
    }

    Serial.print("Connected with IP address: ");
    Serial.println(WiFi.localIP());

    server.begin();
}


void loop() {
    WiFiClient client = server.available();

    if (client) {
        process(client);
        client.stop();
    }

    delay(50);
}


void process(WiFiClient client) {
    String req_type = client.readStringUntil(' ');
    req_type.trim();

    String url = client.readStringUntil(' ');
    url.trim();

    if (url.startsWith("/led/") && (url.length() == 6 || (url.length() == 7 && url.substring(6) == "/"))) {
        String led_val = url.substring(5);

        Serial.print("[DEBUG] LED Value: ");
        Serial.println(led_val);

        if (led_val == "0" || led_val == "1") {
            int int_val = led_val.toInt();
            digitalWrite(LED_PIN, int_val);
            printResponse(client, 200, senMlEncode("led", int_val));
        }
    }
    else if (url == "/temperature" || url == "/temperature/") {
        
    }

    return;
}


void printResponse(WiFiClient client, int code, String body) {
    client.println("HTTP/1.1 " + String(code));

    if (client == 200) {
        client.println("Content-type: application/json; charset=utf-8");
        client.println();
        client.println(body);
    } else {
        client.println();
    }
}


String senMlEncode(String dev, int val) {
    String unit;

    if (dev == "temperature") {
        unit = "\"Cel\""
    } else {
        unit = "null";
    }

    String res = "
        {
            \"bn\": \"arduino_group_3\",
            \"e\": [
                \"n\": \"" + dev + "\",
                \"t\": \"" + String(millis()) + "\",
                \"v\": \"" + String(val) + "\",
                \"u\": "+ unit +",
            ]
        }
    ";
}