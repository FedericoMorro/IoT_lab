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
double temperature;


// Functions prototypes
void process(WiFiClient client);
void printResponse(WiFiClient client, int code, String body);
String senMlEncode(String dev, float val);


void setup() {
    Serial.begin(9600);

    pinMode(TEMPERATURE_PIN, INPUT);
    pinMode(LED_PIN, OUTPUT);

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
    // String will be of the type "GET /led/1"
    String req_type = client.readStringUntil(' ');
    req_type.trim();

    String url = client.readStringUntil(' ');
    url.trim();

    if (! (req_type == "GET")) {
        printResponse(client, 501, "");
        return;
    }

    if (url.startsWith("/led/")) {
        String led_val = url.substring(5);
        // Check that the url is: /led/0 or /led/0/ or /led/1 or /led/1/
        if (! ((led_val == "0" || led_val == "1") && (url.length() == 6 || (url.length() == 7 && url.substring(6) == "/")))) {
            printResponse(client, 400, "");
            return;   
        }
        
        int int_val = led_val.toInt();
        digitalWrite(LED_PIN, int_val);

        Serial.print("[DEBUG] LED Value: "); Serial.println(led_val);
        printResponse(client, 200, senMlEncode("led", (double) int_val));
    }
    else if (url.startsWith("/temperature")) {
        // Check that the url is: /temperature or /temperature/
        if (! (url.length() == 12 || (url.length() == 13 && url.substring(12) == "/"))) {
            printResponse(client, 400, "");
            return;
        }

        double v = (double) analogRead(TEMPERATURE_PIN);
        double r = (1023.0 / v - 1.0) * (double)R1;
        temperature = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;

        Serial.print("[DEBUG] Measured temperature: "); Serial.println(temperature);
        printResponse(client, 200, senMlEncode("temperature", (float) temperature));
    }
    else {
        printResponse(client, 404, "");
    }

    return;
}


void printResponse(WiFiClient client, int code, String body) {
    client.println("HTTP/1.1 " + String(code));

    if (code == 200) {
        client.println("Content-type: application/json; charset=utf-8");
        client.println();
        client.println(body);
    } else {
        client.println();
    }
}


String senMlEncode(String dev, float val) {
    String unit;

    if (dev == "temperature") {
        unit = "\"Cel\"";
    } else {
        unit = "null";
    }

    String res = "\
        {\
            \"bn\": \"ArduinoGroup3\",\
            \"e\": [\
                \"n\": \"" + dev + "\",\
                \"t\": " + String(int(millis()/1000)) + ",\
                \"v\": " + String(val) + ",\
                \"u\": "+ unit +",\
            ]\
        }\
    ";

    return res;
}