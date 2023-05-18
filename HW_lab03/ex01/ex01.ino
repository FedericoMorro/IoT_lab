#include <WiFiNINA.h>
#include "arduino_secrets.h"

char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;

int status = WL_IDLE_STATUS;

char server_address[] = "";
char server_port[]    = "";

WifIClient wifi;
HttpClient client = HttpClient(wifi, server_address, server_port);

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
    client.beginRequest();
    client.post("/log");
    client.sendHeader("Content-Type", "application.json");
    client.sendHeader("Content-Length", body.length());
    client.beginBody();
    client.print(body);
    client.endRequest();
    int ret = client.responseStatusCode();
}
