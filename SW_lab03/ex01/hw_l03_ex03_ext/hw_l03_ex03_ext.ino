#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "arduino_secrets.h"


// Pins
#define TEMPERATURE_PIN A0
#define LED_PIN 2

#define CHECK_MQTT_MSG_INTERVAL   500   // ms
#define REFRESH_CATALOG_INTERVAL  20000 // ms
#define MQTT_PUB_INTERVAL         10000 // ms

// Temperature sensor
const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;
double temperature;

// Led
uint8_t led_state;

// Id
char device_id[] = "IoT_G3_Ard";

// WiFi
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
int status = WL_IDLE_STATUS;
WiFiClient wifi;

// Catalog
char catalog_address[] = "192.168.151.123";    // to be modified
int catalog_port = 8080;
HttpClient http_client = HttpClient(wifi, catalog_address, catalog_port);
String catalog_base_topic;

// Broker
String broker_address;
int broker_port;

// MQTT
const String base_topic = "/tiot/g03/ard";
String body;
bool first_sub = true;

// Json
const int capacity_sen_ml = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument json_sent_sen_ml(capacity_sen_ml);
DynamicJsonDocument json_received_sen_ml(capacity_sen_ml);

const int capacity_cat = JSON_OBJECT_SIZE(6) + JSON_ARRAY_SIZE(1) + 100;
DynamicJsonDocument json_received_catalog(capacity_cat);

const int capacity_cat_subscription = JSON_OBJECT_SIZE(6) + JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(4) + 200;
DynamicJsonDocument json_sent_catalog(capacity_cat_subscription);


// Function prototypes
void refresh_catalog_subscription();
void publish_temperature_reading();
void check_mqtt_msg();
void mqtt_reconnect();
void get_mqtt_broker();
String sen_ml_encode(String dev, float val, String unit);


// Callback definition
void callback(char *topic, byte *payload, unsigned int length) {

    Serial.println(String("Message received on topic: ") + topic);

    if (String(topic) == catalog_base_topic + String("/") + String(device_id)) {
        DeserializationError err = deserializeJson(json_received_catalog, (char *) payload);

        if (err) {
            Serial.print("deserializeJson() failed with code: ");
            Serial.println(err.c_str());
        }

        if (json_received_catalog["in"]["e"] == 0) {
            Serial.println("[DEBUG] Refreshed subscribtion to Catalog");
            return;
        } else {
            Serial.println("[DEBUG] Error in refresh to Catalog");
            refresh_catalog_subscription();
        }

    }
    else if (String(topic) == base_topic + String("/led")) {
        DeserializationError err = deserializeJson(json_received_sen_ml, (char *) payload);

        if (err) {
            Serial.print("deserializeJson() failed with code: ");
            Serial.println(err.c_str());
        }

        if (json_received_sen_ml["e"][0]["n"] == "led") {
            if (json_received_sen_ml["e"][0]["v"] == 1) {
                led_state = 1;
            } else if (json_received_sen_ml["e"][0]["v"] == 0) {
                led_state = 0;
            }
            digitalWrite(LED_PIN, led_state);
        }
    }   
}

// PubSub client
PubSubClient mqtt_client(wifi);
//PubSubClient client(broker_address.c_str(), broker_port, callback, wifi);

int tim_check_mqtt_msg;
int tim_refresh_catalog;
int tim_mqtt_pub;


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
    mqtt_client.setServer(broker_address.c_str(), broker_port);
    mqtt_client.setCallback(callback);

    tim_check_mqtt_msg = millis();
    tim_refresh_catalog = millis();
    tim_mqtt_pub = millis();
}


void loop() {

    if (millis() - tim_refresh_catalog > REFRESH_CATALOG_INTERVAL) {
        refresh_catalog_subscription();
        tim_refresh_catalog = millis();
    }

    if (millis() - tim_mqtt_pub > MQTT_PUB_INTERVAL) {
        publish_temperature_reading();
        tim_mqtt_pub = millis();
    }

    if (millis() - tim_check_mqtt_msg > CHECK_MQTT_MSG_INTERVAL) {
        check_mqtt_msg();
        tim_check_mqtt_msg = millis();
    }

    delay(50);
}


void publish_temperature_reading() {    
    // Read temperature
    double v = (double) analogRead(TEMPERATURE_PIN);
    double r = (1023.0 / v - 1.0) * (double)R1;
    temperature = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;
    Serial.print("[DEBUG] Measured temperature: "); Serial.println(temperature);

    // Create body
    body = sen_ml_encode("temperature", (float) temperature, "Cel");

    // Publish temperature reading
    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
    }
    mqtt_client.publish((base_topic + String("/temp")).c_str(), body.c_str());
}


void refresh_catalog_subscription() {
    String output;

    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
    }

    // Create body
    json_sent_catalog.clear();
    json_sent_catalog["id"] = device_id;
    // insert end_points
    json_sent_catalog["ep"]["m"]["p"][0]["v"] = base_topic + String("/temp");
    json_sent_catalog["ep"]["m"]["p"][0]["t"] = "t";
    json_sent_catalog["ep"]["m"]["s"][0]["v"] = base_topic + String("/led");
    json_sent_catalog["ep"]["m"]["s"][0]["t"] = "l";
    // insert resources
    json_sent_catalog["rs"][0]["n"] = "temperature";
    json_sent_catalog["rs"][0]["t"] = "t";
    json_sent_catalog["rs"][1]["n"] = "led";
    json_sent_catalog["rs"][1]["t"] = "l";

    serializeJson(json_sent_catalog, output);

    Serial.println(output);

    // Publish the subscription
    if (first_sub) {
        mqtt_client.publish((catalog_base_topic + String("/sub")).c_str(), output.c_str());
        first_sub = false;
        Serial.println("[DEBUG] Try subscribtion to Catalog");
    } else {
        mqtt_client.publish((catalog_base_topic + String("/upd")).c_str(), output.c_str());
        Serial.println("[DEBUG] Try refresh to Catalog");
    }
}


void check_mqtt_msg() {
  
    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
    }

    // Check if there are new message on subscribed topics (-> callback)
    mqtt_client.loop();
}


void mqtt_reconnect() {
    // Loop until connected
    while (mqtt_client.state() != MQTT_CONNECTED) {
        if (mqtt_client.connect(device_id)) {     // unique client id

            // Subscribe to led topic
            mqtt_client.subscribe((base_topic + String("/led")).c_str());

            // Subscribe to catalog to get response
            mqtt_client.subscribe((catalog_base_topic + String("/") + String(device_id)).c_str());
        }
        else {
            Serial.print("failed, rc=");
            Serial.print(mqtt_client.state());
            Serial.println(" try again in 5 seconds");
            delay(5000);
        }
    }
}


void get_mqtt_broker() {
    int return_code = -1;

    while (return_code != 200) {
        Serial.println("GET request...");

        http_client.get("/");
        return_code = http_client.responseStatusCode();

        Serial.println("Response code: " + return_code);
    }

    body = http_client.responseBody();

    DeserializationError err = deserializeJson(json_received_catalog, body.c_str());

    if (err) {
        Serial.print("deserializeJson() failed with code: ");
        Serial.println(err.c_str());
    }

    const char *tmp = json_received_catalog["ep"]["m"]["hn"][0]["v"];
    broker_address = String(tmp);
    broker_port = json_received_catalog["ep"]["m"]["pt"][0]["v"];

    tmp = json_received_catalog["ep"]["m"]["bt"][0]["v"];
    catalog_base_topic = String(tmp) + String("/devices");

    Serial.print("[DEBUG] Broker info: "); Serial.print(broker_address); Serial.print(":"); Serial.println(broker_port);
}


String sen_ml_encode(String dev, float val, String unit) {
    String output;

    json_sent_sen_ml.clear();
    json_sent_sen_ml["bn"] = device_id;
    json_sent_sen_ml["e"][0]["n"] = dev;
    json_sent_sen_ml["e"][0]["t"] = int(millis()/1000);
    json_sent_sen_ml["e"][0]["v"] = val;
    json_sent_sen_ml["e"][0]["u"] = unit;

    serializeJson(json_sent_sen_ml, output);
    return output;
}