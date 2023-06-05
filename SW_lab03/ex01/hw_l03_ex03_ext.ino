#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "arduino_secrets.h"


// Pins
#define TEMPERATURE_PIN A0

#define LED_PIN 2


// Temperature sensor
const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;
double temperature;

// Led
uint8_t led_state;

// WiFi
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
int status = WL_IDLE_STATUS;
WiFiClient wifi;

// Catalog
char catalog_address[] = "192.168.255.123";    // to be modified
int catalog_port = 8080;
HttpClient http_client = HttpClient(wifi, catalog_address, catalog_port);

// Broker
String broker_address = "test.mosquitto.org";
int broker_port = 1883;

// MQTT
const String base_topic = "/IoT_lab/group3";
String body;

// Json
const int capacity = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument doc_snd_sen_ml(capacity);
DynamicJsonDocument doc_rec_sen_ml(capacity);

// Callback definition
void callback(char *topic, byte *payload, unsigned int length) {
    
    DeserializationError err = deserializeJson(doc_rec_sen_ml, (char *) payload);

    if (err) {
        Serial.print("deserializeJson() failed with code: ");
        Serial.println(err.c_str());
    }

    if (doc_rec_sen_ml["e"][0]["n"] == "led") {
        if (doc_rec_sen_ml["e"][0]["v"] == 1) {
            led_state = 1;
        } else if (doc_rec_sen_ml["e"][0]["v"] == 0) {
            led_state = 0;
        }
        digitalWrite(LED_PIN, led_state);
    }
}

// PubSub client
PubSubClient *mqtt_client;
//PubSubClient client(broker_address.c_str(), broker_port, callback, wifi);


// Function prototypes
void get_mqtt_broker();
void reconnect();
String sen_ml_encode(String dev, float val, String unit);


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

    get_mqtt_broker();
}


void loop() {

    if (mqtt_client.state() != MQTT_CONNECTED) {
        reconnect();
    }

    // Read temperature
    double v = (double) analogRead(TEMPERATURE_PIN);
    double r = (1023.0 / v - 1.0) * (double)R1;
    temperature = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;
    Serial.print("[DEBUG] Measured temperature: "); Serial.println(temperature);

    // Create body
    body = sen_ml_encode("temperature", (float) temperature, "Cel");

    // Publish temperature reading
    mqtt_client.publish((base_topic + String("/temperature")).c_str(), body.c_str());
    
    // Check if there are new message on subscribed topics (-> callback)
    mqtt_client.loop();

    delay(50);
}


void get_mqtt_broker() {
    int return_code = -1;

    while (return_code != 200) {
        client.beginRequest();
        client.get("/MQTTbroker");
        client.endRequest();
        return_code = client.responseStatusCode();
    }

    body = client.responseBody();
}


void reconnect() {
    // Loop until connected
    while (mqtt_client.state() != MQTT_CONNECTED) {
        if (mqtt_client.connect("TiotGroup3")) {     // unique client id
            // Subscribe to led topic
            mqtt_client.subscribe((base_topic + String("/led")).c_str());
        }
        else {
            Serial.print("failed, rc=");
            Serial.print(mqtt_client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}


String sen_ml_encode(String dev, float val, String unit) {
    String output;

    doc_snd_sen_ml.clear();
    doc_snd_sen_ml["bn"] = "ArduinoGroup3";
    doc_snd_sen_ml["e"][0]["n"] = dev;
    doc_snd_sen_ml["e"][0]["t"] = int(millis()/1000);
    doc_snd_sen_ml["e"][0]["v"] = val;
    doc_snd_sen_ml["e"][0]["u"] = unit;

    serializeJson(doc_snd_sen_ml, output);
    return output;
}