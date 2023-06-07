#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include "arduino_secrets.h"
#include <MBED_RPi_Pico_TimerInterrupt.h>


#define REFRESH_TIME 60000000L // in microseconds

// Pins
#define TEMPERATURE_PIN A0


MBED_RPI_PICO_Timer ITimer1(1);

// WiFi
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;

int status = WL_IDLE_STATUS;

char server_address[] = "192.168.255.123";    // to be modified
int server_port = 8080;
String body;

WiFiClient wifi;
HttpClient client = HttpClient(wifi, server_address, server_port);


// Temperature sensor
const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;
double temperature;


// Functions prototypes
String registering_payload_encode();
int registering();
void refreshing(uint alarm_num);


void setup() {
    Serial.begin(9600);

    pinMode(TEMPERATURE_PIN, INPUT);

    while (status != WL_CONNECTED) {
        Serial.print("Attempting to connect to SSID: ");
        Serial.println(ssid);

        status = WiFi.begin(ssid, pass);
        delay(2000);
    }

    Serial.print("Connected with IP address: ");
    Serial.println(WiFi.localIP());
    ITimer1.setInterval(REFRESH_TIME, refreshing);
}


void loop() {

    // Read the temperature
    double v = (double) analogRead(TEMPERATURE_PIN);
    double r = (1023.0 / v - 1.0) * (double)R1;
    temperature = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;
    Serial.print("[DEBUG] Measured temperature: "); Serial.println(temperature);

    int ret = registering();

    Serial.print("[DEBUG] Response code: " + String(ret) + "\n");

    // Try to re-send if error, otherwise wait for next misuration
    if (ret == 200) {
        delay(5000);
    } else {
        delay(1000);
    }
}


String registering_payload_encode() {
    String res = "{\
        \"id\": \"ArduinoGroup3\",\
        \"ep\": {\
            \"r\": [\
                \"r\": [\
                    {\"v\": \"127.0.0.1:8080/0\"},\
                    {\"v\": \"127.0.0.1:8080/1\"}
                ],
                \"c\": [
                    {\"v\": \"127.0.0.1:8080/2\"}
                ]
            ],\
            \"m\": [\
                \"s\": [
                    {\"v\": \"/tiot/g03/dev/0\"}
                ],\
                \"p\": [\
                    {\"v\": \"/tiot/g03/dev/1\"},
                    {\"v\": \"/tiot/g03/dev/2\"}
                ]\
            ],\
        }\
        \"in\": {\
            \"r\": [\
                {\"n\": \"temp\"\}\
            ]\
        }\
    }";
    Serial.print(res + " "); Serial.println(res.length());

    return res;
}


int registering() {
    Serial.println("[DEBUG] POST request: registering...");
    // Create the body
    body = registering_payload_encode();

    // Send the request
    client.beginRequest();
    client.post("/devices/sub");

    /* 
    * change session_id in the cookie header according to postman session_id, it will be
    * automatically reassigned at the first request it makes
    * 
    * we use postman session_id so that with a GET request from postman we can see the
    * log, otherwise, the requests of the Arduino will be saved in another log session
    * used just for Arduino
    *
    * using the same session_id, although it is probably a very bad practice, allows us
    * to have no issue in visualizing the log
    */
    // client.sendHeader("Cookie", "session_id=629edc8b148df01e95e953b8641c53fc3c6959f4"); -> session not used
    client.sendHeader("Content-Type", "application/json");
    client.sendHeader("Content-Length", body.length());
    client.beginBody();
    client.print(body);
    client.endRequest();
  
    int ret = client.responseStatusCode();
    Serial.print("[DEBUG] POST request response code: "); Serial.println(ret);
    Serial.println();

    return ret;
}


void refreshing(uint alarm_num) {
    TIMER_ISR_START(alarm_num);
    Serial.println("[DEBUG] PUT request: updating...");

    // Create the body
    body = registering_payload_encode();

    String content_type = "application/json";

    // Send the request
    client.beginRequest();
    client.put("/devices/upd", content_type, body);
  
    int ret = client.responseStatusCode();
    Serial.print("[DEBUG] PUT request response code: "); Serial.println(ret);
    Serial.println();

    TIMER_ISR_END(alarm_num);
}