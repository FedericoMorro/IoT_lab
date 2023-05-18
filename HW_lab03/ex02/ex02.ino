#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include "arduino_secrets.h"


// WiFi
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;

int status = WL_IDLE_STATUS;

WiFiServer server(80);


// Functions prototypes
void process(WiFiClient client);
void printResponse(WiFiClient client, int code, String body);


void setup() {
    Serial.begin(9600);

    while (status != WL_CONNECTED) {
        Serial.print("Attempting to connect to SSID: ")
        Serial.println(ssid);

        status = WiFi.begin(ssid, pass);
        delay(2000);
    }

    Serial.print("Connected with IP address: ");
    Serial.println(WiFi.localIP());
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

    if (url.startWith("/led/")) {
        String led_val = url.substring(5);

        Serial.print("[DEBUG] LED Value: ");
        Serial.println(led_val);

        if (led_val == "0" || led_val == "1") {
            int int_val = led_val.toInt();
            digitalWrtie(LED_PIN, int_val);
            printResponse(client, 200, senMlEncode("led", int_val, ""));
        }
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