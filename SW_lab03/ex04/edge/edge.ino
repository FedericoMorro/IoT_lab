#include <PDM.h>
#include <LiquidCrystal_PCF8574.h>
#include <Wire.h>

#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "arduino_secrets.h"


#define SERIAL_DEBUG 1

/*
 * INTERNAL DATA TYPE DECLARATION AND DEFINITION
 */
struct pub_resource {
  String name, type, ep;
};

struct sub_resource {
    String name, type, ep;
    void (*res_callback)(byte *, unsigned int);
};

#define N_PUB_RES 3
#define N_SUB_RES 3

#define PUB_IND_TEMP 0
#define PUB_IND_PIR  1
#define PUB_IND_MIC  2

void ac_callback(byte *payload, unsigned int length);
void ht_callback(byte *payload, unsigned int length);
void lcd_callback(byte *payload, unsigned int length);

pub_resource pub_res[N_PUB_RES] = {
    {"temperature", "t", "/t"},
    {"pir_presence", "p", "/p"},
    {"mic_presence", "m", "/m"}
};

#define SUB_IND_AC   0
#define SUB_IND_HT   1
#define SUB_IND_LCD  2

sub_resource sub_res[N_SUB_RES] = {
    {"air_cond", "a", "/a", &ac_callback},
    {"heating", "h", "/h", &ht_callback},
    {"lcd", "l", "/l", &lcd_callback}
};
/*
 * END INTERNAL DATA TYPE DECLARATION AND DEFINITION
 */

/*
 *  CONNECTIVITY FUCNTIONS AND VARIABLES DECLARATIONS
 */

#define CATALOG_TIMEOUT 60000

// Id
char device_id[] = "ard";

// WiFi
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
int status = WL_IDLE_STATUS;
WiFiClient wifi;

// Catalog
char catalog_address[] = "192.168.134.123";    // to be modified
int catalog_port = 8080;
HttpClient http_client = HttpClient(wifi, catalog_address, catalog_port);
String catalog_base_topic;

// Broker
String broker_address;
int broker_port;

// MQTT
const String base_topic = "/tiot/g03/" + String(device_id);
String body;
bool first_sub = true;

// PubSub client
PubSubClient mqtt_client(wifi);

int tim_check_mqtt_msg;
int tim_refresh_catalog;
int tim_mqtt_pub;

// JSON
const int capacity_sen_ml = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 1000;
DynamicJsonDocument json_sent_sen_ml(capacity_sen_ml);
DynamicJsonDocument json_received_sen_ml(capacity_sen_ml);

const int capacity_cat = JSON_OBJECT_SIZE(6) + JSON_ARRAY_SIZE(1) + 1000;
DynamicJsonDocument json_received_catalog(capacity_cat);

const int capacity_cat_subscription = JSON_OBJECT_SIZE(6) + JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(4) + 2000;
DynamicJsonDocument json_sent_catalog(capacity_cat_subscription);


// Function prototypes
void connectivity_setup();

void get_mqtt_broker();
void mqtt_reconnect();
void refresh_catalog_subscription();
void check_mqtt_msg();
String sen_ml_encode(String dev, double val, String unit);

void callback(char *topic, byte *payload, unsigned int length);
/*
 *  END CONNECTIVITY FUNCTIONS AND VARIABLES DECLARATIONS
 */

#define TEMPERATURE_PIN A0

#define FAN_PIN       4
#define RED_LED_PIN   2
#define GREEN_LED_PIN 21
#define PIR_PIN       7

#define SAMPLE_BUFFER_SIZE      256
#define BUFFER_SIZE_SAMPLES_CNT 100

// Temperature
double v;
const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;
double temperature;

// Air conditioning (fan)
uint8_t air_conditioning_intensity;

// Heating system (red led)
uint8_t heating_intensity;

// Presence flag
uint8_t presence;

// Pir sensor
uint8_t pir_presence;
void pir_presence_isr();

// Microphone
uint8_t microphone_presence;
const uint8_t n_sound_events = 10;   // tbc
const int sound_threshold = 10000;    // tbc
const int sound_interval = 20 * 1000;   //60 * 60 * 1000;
short sample_buffer[SAMPLE_BUFFER_SIZE];      // buffer to read sample into, each sample is 16-bit
void on_PDM_data();
int current_samples_read_cnt;
int microphone_time;
const int single_event_duration = 100;      // ms
int buffer_past_samples_cnt[BUFFER_SIZE_SAMPLES_CNT];
int current_pos;

int tim_sound;

void loop_update_audio_samples_cnt();

// Display
LiquidCrystal_PCF8574 lcd(0x20);
char lcd_buffer[2][21];
void loop_refresh_display();
uint8_t display_state;


void setup() {
    Serial.begin(9600);
    while (!Serial);
    #if SERIAL_DEBUG
        Serial.println("[DEBUG] Smart Home systems starting...");
    #endif // SERIAL_DEBUG


    /* PIN SETUP */
    pinMode(TEMPERATURE_PIN, INPUT);

    pinMode(FAN_PIN, OUTPUT);
    pinMode(RED_LED_PIN, OUTPUT);
    pinMode(GREEN_LED_PIN, OUTPUT);

    pinMode(PIR_PIN, INPUT);
    /* END PIN SETUP */


    connectivity_setup();


    /* PIR AND MIC PRESENCE SETUP */
    presence = 0;
    
    attachInterrupt(digitalPinToInterrupt(PIR_PIN), pir_presence_isr, CHANGE);
    pir_presence = 0;

    air_conditioning_intensity = 0;
    heating_intensity = 0;
    
    PDM.onReceive(on_PDM_data);   // callback function (ISR)
    if (!PDM.begin(1, 16000)) {     // mono, 16 kHz sample frequency
        Serial.println("Failed to start PDM");
        while (1);
    }
    microphone_presence = 0;
    current_samples_read_cnt = 0;
    microphone_time = 0;
    for (int i=0; i<BUFFER_SIZE_SAMPLES_CNT; i++) {
        buffer_past_samples_cnt[i] = 0;
    }
    current_pos = 0;
    
    tim_sound = millis();
    /* END PIR AND MIC PRESENCE SETUP */


    /* LCD SCREEN SETUP */
    Wire.begin();
    Wire.beginTransmission(0x27);
    lcd.begin(16, 2);
    lcd.setBacklight(255);
    display_state = 1;
    /* END LCD SCREEN SETUP */
}


void loop() {
    if (millis() - tim_refresh_catalog >= CATALOG_TIMEOUT) {
        refresh_catalog_subscription();
    }

    compute_temperature();

    // pir presence timeout moved to Controller.py

    Serial.print("[DEBUG] PIR presence: "); Serial.print(pir_presence);
    Serial.print(";\tMicrophone presence: "); Serial.println(microphone_presence);

    if (millis() - tim_sound >= sound_interval / BUFFER_SIZE_SAMPLES_CNT) {
        loop_update_audio_samples_cnt();
        tim_sound = millis();
    }
    
    delay(2000);
}


void compute_temperature() {
    double v = (double) analogRead(TEMPERATURE_PIN);
    double r = (1023.0 / v - 1.0) * (double)R1;
    temperature = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;
    Serial.print("[DEBUG] Measured temperature: "); Serial.println(temperature);
    
    String output = sen_ml_encode(pub_res[PUB_IND_TEMP].name, temperature, "Cel");

    mqtt_client.publish((base_topic + pub_res[PUB_IND_TEMP].ep).c_str(), output.c_str());
}


void pir_presence_isr() {
    uint8_t prev_pir_pres = pir_presence;
    pir_presence = 1;

    String output = sen_ml_encode(pub_res[PUB_IND_PIR].name, pir_presence, "");

    if (pir_presence != prev_pir_pres) {
        mqtt_client.publish((base_topic + pub_res[PUB_IND_PIR].ep).c_str(), output.c_str());
    }
}


void on_PDM_data() {
    int bytes_available = PDM.available();
    PDM.read(sample_buffer, bytes_available);

    int found = 0;
    for (int i=0; i<SAMPLE_BUFFER_SIZE && !found; i++) {
        if (sample_buffer[i] > sound_threshold) {
            found = 1;
        }
    }

    if (found && millis() - microphone_time > single_event_duration) {
        current_samples_read_cnt++;
        microphone_time = millis();
    }
}


void loop_update_audio_samples_cnt() {
    buffer_past_samples_cnt[current_pos] = current_samples_read_cnt;
    current_pos = (current_pos + 1) % BUFFER_SIZE_SAMPLES_CNT;
    current_samples_read_cnt = 0;

    int sum = 0;
    for (int i=0; i<BUFFER_SIZE_SAMPLES_CNT; i++) {
        sum += buffer_past_samples_cnt[i];
    }
    Serial.print("Sum of buffer cnt :"); Serial.println(sum);

    uint8_t prev_mic_pres = microphone_presence;
    microphone_presence = (sum >= n_sound_events) ? 1:0;


    if (prev_mic_pres != microphone_presence) {
        String output = sen_ml_encode(pub_res[PUB_IND_MIC].name, microphone_presence, "");
        mqtt_client.publish((base_topic + pub_res[PUB_IND_MIC].ep).c_str(), output.c_str());
    }
}


/*
 * CONNECTIVITY FUNCTIONS
 */

void callback(char *topic, byte *payload, unsigned int length) {
    #if SERIAL_DEBUG
        Serial.println(String("Message received on topic: ") + topic);
    #endif

    String topic_string = String(topic);
    for (int i = 0; i < N_SUB_RES; i++) {
        if (topic_string == (base_topic + sub_res[i].ep)) {
            sub_res[i].res_callback(payload, length);
        }
    }

    return;  
}


void ac_callback(byte *payload, unsigned int length) {
    DeserializationError err = deserializeJson(json_received_sen_ml, (char *)payload);

    if (err) {
        Serial.print("deserializeJson() failed with code: ");
        Serial.println(err.c_str());
        return;
    }

    const char *tmp = json_received_sen_ml["e"][0]["n"];
    if (String(tmp) == sub_res[SUB_IND_AC].name) {
        analogWrite(FAN_PIN, (int)json_received_sen_ml["e"][0]["v"]);
    }

    return;
}


void ht_callback(byte *payload, unsigned int length) {
    DeserializationError err = deserializeJson(json_received_sen_ml, (char *)payload);

    if (err) {
        Serial.print("deserializeJson() failed with code: ");
        Serial.println(err.c_str());
        return;
    }

    const char *tmp = json_received_sen_ml["e"][0]["n"];
    if (String(tmp) == sub_res[SUB_IND_HT].name) {
        analogWrite(RED_LED_PIN, (int)json_received_sen_ml["e"][0]["v"]);
    }

    return;
}


void lcd_callback(byte *payload, unsigned int length) {
    DeserializationError err = deserializeJson(json_received_sen_ml, (char *)payload);

    if (err) {
        Serial.print("deserializeJson() failed with code: ");
        Serial.println(err.c_str());
        return;
    }

    uint8_t flg = 0;
    const char *tmp_top = json_received_sen_ml["e"][0]["n"];
    if (String(tmp_top) == sub_res[SUB_IND_LCD].name) {
        const char *tmp = json_received_sen_ml["e"][0]["v"];
        sprintf(lcd_buffer[0], tmp);
        flg++;
    }

    const char *tmp_top2 = json_received_sen_ml["e"][0]["n"];
    if (String(tmp_top2) == sub_res[SUB_IND_LCD].name) {
        const char *tmp = json_received_sen_ml["e"][0]["v"];
        sprintf(lcd_buffer[1], tmp);
        flg++;
    }

    if (flg == 2) {
        lcd.setCursor(0, 0);
        lcd.print(lcd_buffer[0]);
        lcd.setCursor(0, 1);
        lcd.print(lcd_buffer[1]);
    } else {
        Serial.println("[LCD] Corrupted payload received from MQTT server. Skipping LCD refresh.");
    }

    return;
}


void connectivity_setup() {
    while (status != WL_CONNECTED) {
        Serial.print("Attempting to connect to SSID: ");
        Serial.println(ssid);

        status = WiFi.begin(ssid, pass);
        delay(1000);
    }

    Serial.print("Connected with IP address: ");
    Serial.println(WiFi.localIP());

    // Create mqtt client
    get_mqtt_broker();
    mqtt_client.setServer(broker_address.c_str(), broker_port);
    mqtt_client.setCallback(callback);

    #if SERIAL_DEBUG
        Serial.println(broker_address + " " + broker_port);
    #endif

    tim_check_mqtt_msg = millis();
    tim_refresh_catalog = millis();
    tim_mqtt_pub = millis();

    refresh_catalog_subscription();
}


void check_mqtt_msg() {
  
    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
    }

    // Check if there are new message on subscribed topics (-> callback)
    mqtt_client.loop();
}


void get_mqtt_broker() {
    int return_code = -1;

    while (return_code != 200) {
        #if SERIAL_DEBUG
            Serial.println("[DEBUG] GET request...");
        #endif

        http_client.get("/");
        return_code = http_client.responseStatusCode();

        #if SERIAL_DEBUG
            Serial.println("Response code: " + return_code);
        #endif
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

    const char *tmp_ = json_received_catalog["ep"]["m"]["bt"][0]["v"];
    catalog_base_topic = String(tmp_) + String("/devices");

    #if SERIAL_DEBUG
        Serial.println("[DEBUG] Broker info: " + broker_address + ":" + broker_port + "; base_topic: " + catalog_base_topic);
    #endif
}


void mqtt_reconnect() {
    // Loop until connected
    while (mqtt_client.state() != MQTT_CONNECTED) {
        String unique_device_id = String("IoT_Lab_G3_") + String(device_id);
        if (mqtt_client.connect(unique_device_id.c_str())) {     // unique client id

            // Subscribe to led topic
            mqtt_client.subscribe((base_topic + String("/led")).c_str());

            for (int i = 0; i < N_SUB_RES; i++) {
                mqtt_client.subscribe((base_topic + String(sub_res[i].ep)).c_str());
            }

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


void refresh_catalog_subscription() {
    String output;

    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
    }

    #if SERIAL_DEBUG
        Serial.println("Connected to MQTT");
    #endif

    /*
     * pub: /temp, /pir, /mic
     * sub: /ac, /ht, /lcd
     */

    // Create body
    json_sent_catalog.clear();
    json_sent_catalog["id"] = device_id;

    for (int i = 0; i < N_PUB_RES; i++) {
        json_sent_catalog["ep"]["m"]["p"][i]["v"] = base_topic + pub_res[i].ep;
        json_sent_catalog["ep"]["m"]["p"][i]["t"] = pub_res[i].type;
        json_sent_catalog["rs"][i]["n"] = pub_res[i].name;
        json_sent_catalog["rs"][i]["t"] = pub_res[i].type;
    }

    for (int i = 0; i < N_SUB_RES; i++) {
        json_sent_catalog["ep"]["m"]["s"][i]["v"] = base_topic + sub_res[i].ep;
        json_sent_catalog["ep"]["m"]["s"][i]["t"] = sub_res[i].type;
        json_sent_catalog["rs"][i + N_PUB_RES]["n"] = sub_res[i].name;
        json_sent_catalog["rs"][i + N_PUB_RES]["t"] = sub_res[i].type;
    }

    serializeJson(json_sent_catalog, output);

    #if SERIAL_DEBUG
        Serial.println("[DEBUG] " + output);
    #endif

    // Publish the subscription
    if (first_sub) {
        mqtt_client.publish((catalog_base_topic + String("/sub")).c_str(), output.c_str());
        first_sub = false;
        Serial.println("[DEBUG] Try subscribtion to Catalog");
    } else {
        mqtt_client.publish((catalog_base_topic + String("/upd")).c_str(), output.c_str());
        Serial.println("[DEBUG] Try refresh to Catalog");
    }

    // Check if there are new message on subscribed topics (-> callback)
    mqtt_client.loop();
}


String sen_ml_encode(String dev, double val, String unit) {
    String output;

    json_sent_sen_ml.clear();
    json_sent_sen_ml["bn"] = device_id;
    json_sent_sen_ml["e"][0]["n"] = dev;
    json_sent_sen_ml["e"][0]["t"] = int(millis()/1000);
    json_sent_sen_ml["e"][0]["v"] = val;
    if (unit == "None") {
        json_sent_sen_ml["e"][0]["u"] = "";
    } else {
        json_sent_sen_ml["e"][0]["u"] = unit;
    }

    serializeJson(json_sent_sen_ml, output);
    return output;
}