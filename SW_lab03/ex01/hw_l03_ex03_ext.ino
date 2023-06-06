#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Scheduler.h>

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

// Id
char device_id[] = "IoT_lab_group3_Arduino";

// WiFi
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
int status = WL_IDLE_STATUS;
WiFiClient wifi;

// Catalog
char catalog_address[] = "192.168.255.123";    // to be modified
int catalog_port = 8080;
HttpClient http_client = HttpClient(wifi, catalog_address, catalog_port);
const String catalog_base_topic = "/IoT_lab/group3/catalog/devices";

// Broker
String broker_address;
int broker_port;

// MQTT
const String base_topic = "/IoT_lab/group3/Arduino";
String body;
bool first_sub = true;

// PubSub client
PubSubClient mqtt_client;
//PubSubClient client(broker_address.c_str(), broker_port, callback, wifi);

// Json
const int capacity_sen_ml = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument doc_snd_sen_ml(capacity_sen_ml);
DynamicJsonDocument doc_rec_sen_ml(capacity_sen_ml);

const int capacity_cat_broker = JSON_OBJECT_SIZE(2) + 100;
DynamicJsonDocument doc_rec_cat_broker(capacity_cat_broker);

const int capacity_cat_subscription = JSON_OBJECT_SIZE(6) + JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(4) + 200;
DynamicJsonDocument doc_snd_cat_sub(capacity_cat_subscription);


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


// Function prototypes
void get_mqtt_broker();
void mqtt_reconnect();
void loop_refresh_catalog_subscription();
String sen_ml_encode(String dev, float val, String unit);


void setup() {
    Serial.begin(9600);

    pinMode(TEMPERATURE_PIN, INPUT);
    pinMode(LED_PIN, OUTPUT);

    // Connect to WiFi
    while (status != WL_CONNECTED) {
        Serial.print("Attempting to connect to SSID: ");
        Serial.println(ssid);

        status = WiFi.begin(ssid, pass);
        delay(2000);
    }

    Serial.print("Connected with IP address: ");
    Serial.println(WiFi.localIP());

    // Create mqtt client
    get_mqtt_broker();
    mqtt_client = PubSubClient(broker_address.c_str(), broker_port, callback, wifi);

    // Initialize scheduler task
    Scheduler.startLoop(loop_refresh_catalog_subscription);
}


void loop() {

    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
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

    DeserializationError err = deserializeJson(doc_rec_cat_broker, body.c_str());

    if (err) {
        Serial.print("deserializeJson() failed with code: ");
        Serial.println(err.c_str());
    }

    broker_address = doc_rec_cat_broker["hostname"];
    broker_port = doc_rec_cat_broker["port"];
}


void mqtt_reconnect() {
    // Loop until connected
    while (mqtt_client.state() != MQTT_CONNECTED) {
        if (mqtt_client.connect(device_id)) {     // unique client id
            // Subscribe to led topic
            mqtt_client.subscribe((base_topic + String("/led")).c_str());

            // Subscribe to catalog to get response
        }
        else {
            Serial.print("failed, rc=");
            Serial.print(mqtt_client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}


void loop_refresh_catalog_subscription() {
    String output;

    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
    }

    // Create body
    doc_snd_cat_sub.clear();
    doc_snd_cat_sub["id"] = device_id;
    doc_snd_cat_sub["end_points"]["MQTT"]["publisher"][0]["value"] = (base_topic + String("/temperature")).c_str();
    doc_snd_cat_sub["end_points"]["MQTT"]["subscriber"][0]["value"] = (base_topic + String("/led")).c_str();
    doc_snd_cat_sub["info"]["resources"][0]["name"] = "pub/temperature";
    doc_snd_cat_sub["info"]["resources"][1]["name"] = "sub/led";

    serializeJson(doc_snd_sen_ml, output);

    // Publish the subscription
    if (first_sub) {
        mqtt_client.publish((catalog_base_topic + String("subscription")).c_str(), output.c_str());
        first_sub = false;
    } else {
        mqtt_client.publish((catalog_base_topic + String("refresh")).c_str(), output.c_str());
    }

    delay(60000);
}


String sen_ml_encode(String dev, float val, String unit) {
    String output;

    doc_snd_sen_ml.clear();
    doc_snd_sen_ml["bn"] = device_id;
    doc_snd_sen_ml["e"][0]["n"] = dev;
    doc_snd_sen_ml["e"][0]["t"] = int(millis()/1000);
    doc_snd_sen_ml["e"][0]["v"] = val;
    doc_snd_sen_ml["e"][0]["u"] = unit;

    serializeJson(doc_snd_sen_ml, output);
    return output;
}