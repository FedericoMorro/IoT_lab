#include <PDM.h>
#include <LiquidCrystal_PCF8574.h>
#include <Wire.h>
#include <Scheduler.h>

#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "arduino_secrets.h"


#define SERIAL_DEBUG 1


struct resource {
    String name, type;
};


resource temp_res = {"temperature", "t"};
resource pir_res = {"pir_presence", "p"};
resource mic_res = {"mic_presence", "m"};

resource ac_res = {"air_cond", "a"};
resource ht_res = {"heating", "h"};
resource lcd_res = {"lcd", "l"};


/*
 *  CONNECTIVITY FUCNTIONS AND VARIABLES DECLARATIONS
 */
// Id
char device_id[] = "ard";

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
const String base_topic;
String body;
bool first_sub = true;

// PubSub client
PubSubClient mqtt_client(wifi);

int tim_check_mqtt_msg;
int tim_refresh_catalog;
int tim_mqtt_pub;

// JSON
const int capacity_sen_ml = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument json_sent_sen_ml(capacity_sen_ml);
DynamicJsonDocument json_received_sen_ml(capacity_sen_ml);

const int capacity_cat = JSON_OBJECT_SIZE(6) + JSON_ARRAY_SIZE(1) + 100;
DynamicJsonDocument json_received_catalog(capacity_cat);

const int capacity_cat_subscription = JSON_OBJECT_SIZE(6) + JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(4) + 200;
DynamicJsonDocument json_sent_catalog(capacity_cat_subscription);


// Function prototypes
void connectivity_setup();

void get_mqtt_broker();
void mqtt_reconnect();
void refresh_catalog_subscription();
void check_mqtt_msg();
String sen_ml_encode(String dev, float val, String unit);

void callback();
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
    Scheduler.startLoop(loop_update_audio_samples_cnt);
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
    compute_temperature();

    // pir presence timeout moved to Controller.py

    Serial.print("[DEBUG] PIR presence: "); Serial.print(pir_presence);
    Serial.print(";\tMicrophone presence: "); Serial.println(microphone_presence);

    
    
    delay(2000);
}


void compute_temperature() {
    double v = (double) analogRead(TEMPERATURE_PIN);
    double r = (1023.0 / v - 1.0) * (double)R1;
    temperature = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;
    Serial.print("[DEBUG] Measured temperature: "); Serial.println(temperature);
    
    // TODO: send to MQTT temp
}


void pir_presence_isr() {
    pir_presence = 1;

    // TODO: update pir value on mqtt
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
        // TODO: send microphone_presence val on MQTT
    }

    delay(sound_interval / BUFFER_SIZE_SAMPLES_CNT);
}


/*
 * CONNECTIVITY FUNCTIONS
 */

void callback(char *topic, byte *payload, unsigned int length) {
    #if SERIAL_DEBUG
        Serial.println(String("Message received on topic: ") + topic);
    #endif

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

    tim_check_mqtt_msg = millis();
    tim_refresh_catalog = millis();
    tim_mqtt_pub = millis();
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

    tmp = json_received_catalog["ep"]["m"]["bt"][0]["v"];
    catalog_base_topic = String(tmp) + String("/devices");
    base_topic = catalog_base_topic + String("/") + String(device_id);

    #if SERIAL_DEBUG
        Serial.println("[DEBUG] Broker info: " + broker_address + ":" + broker_port + "; base_topic: " + base_topic);
    #endif
}


void mqtt_reconnect() {
    // Loop until connected
    while (mqtt_client.state() != MQTT_CONNECTED) {
        String unique_device_id = String("IoT_Lab_G3_") + String(device_id);
        if (mqtt_client.connect(unique_device_id.c_str())) {     // unique client id

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


void refresh_catalog_subscription() {
    String output;

    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
    }

    /*
     * pub: /temp, /pir, /mic
     * sub: /ac, /ht, /lcd
     */

    // Create body
    json_sent_catalog.clear();
    json_sent_catalog["id"] = device_id;

    json_sent_catalog["ep"]["m"]["p"][0]["v"] = base_topic + String("/t");
    json_sent_catalog["ep"]["m"]["p"][0]["t"] = temp_res.type;
    json_sent_catalog["ep"]["m"]["p"][1]["v"] = base_topic + String("/p");
    json_sent_catalog["ep"]["m"]["p"][1]["t"] = pir_res.type;
    json_sent_catalog["ep"]["m"]["p"][2]["v"] = base_topic + String("/m");
    json_sent_catalog["ep"]["m"]["p"][2]["t"] = mic_res.type;

    json_sent_catalog["ep"]["m"]["s"][0]["v"] = base_topic + String("/a");
    json_sent_catalog["ep"]["m"]["s"][0]["t"] = ac_res.type;
    json_sent_catalog["ep"]["m"]["s"][1]["v"] = base_topic + String("/h");
    json_sent_catalog["ep"]["m"]["s"][1]["t"] = ht_res.type;
    json_sent_catalog["ep"]["m"]["s"][2]["v"] = base_topic + String("/l");
    json_sent_catalog["ep"]["m"]["s"][2]["t"] = lcd_res.type;

    json_sent_catalog["rs"][0]["n"] = temp_res.name;
    json_sent_catalog["rs"][0]["t"] = temp_res.type;
    json_sent_catalog["rs"][1]["n"] = pir_res.name;
    json_sent_catalog["rs"][1]["t"] = pir_res.type;
    json_sent_catalog["rs"][2]["n"] = mic_res.name;
    json_sent_catalog["rs"][2]["t"] = mic_res.type;
    json_sent_catalog["rs"][3]["n"] = ac_res.name;
    json_sent_catalog["rs"][3]["t"] = ac_res.type;
    json_sent_catalog["rs"][3]["n"] = ht_res.name;
    json_sent_catalog["rs"][3]["t"] = ht_res.type;
    json_sent_catalog["rs"][4]["n"] = lcd_res.name;
    json_sent_catalog["rs"][4]["t"] = lcd_res.type;

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

    // Check if there are new message on subscribed topics (-> callback)
    mqtt_client.loop();
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