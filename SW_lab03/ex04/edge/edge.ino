#include <PDM.h>
#include <LiquidCrystal_PCF8574.h>
#include <Wire.h>
#include <Scheduler.h>

#include <WiFiNINA.h>
#include <ArduinoHttpClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "arduino_secrets.h"


/*
 *  CONNECTIVITY FUCNTIONS AND VARIABLES DECLARATIONS
 */
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

// PubSub client
PubSubClient mqtt_client(wifi);

int tim_check_mqtt_msg;
int tim_refresh_catalog;
int tim_mqtt_pub;

// Json
const int capacity_sen_ml = JSON_OBJECT_SIZE(2) + JSON_ARRAY_SIZE(1) + JSON_OBJECT_SIZE(4) + 100;
DynamicJsonDocument doc_snd_sen_ml(capacity_sen_ml);
DynamicJsonDocument doc_rec_sen_ml(capacity_sen_ml);

const int capacity_cat = JSON_OBJECT_SIZE(32) + JSON_ARRAY_SIZE(12) + 100;
DynamicJsonDocument doc_rec_cat(capacity_cat);

const int capacity_cat_subscription = JSON_OBJECT_SIZE(6) + JSON_ARRAY_SIZE(2) + JSON_OBJECT_SIZE(4) + 200;
DynamicJsonDocument doc_snd_cat_sub(capacity_cat_subscription);


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

// Input from serial
void change_max_min();

void setup() {
    Serial.begin(9600);
    while (!Serial);
    Serial.println("Lab 2 starting");

    // Pins setup
    pinMode(TEMPERATURE_PIN, INPUT);

    pinMode(FAN_PIN, OUTPUT);
    pinMode(RED_LED_PIN, OUTPUT);
    pinMode(GREEN_LED_PIN, OUTPUT);

    pinMode(PIR_PIN, INPUT);

    connectivity_setup();

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

    Wire.begin();
    Wire.beginTransmission(0x27);
    lcd.begin(16, 2);
    lcd.setBacklight(255);
    display_state = 1;
    Scheduler.startLoop(loop_refresh_display);
}


void loop() {
    v = (double) analogRead(TEMPERATURE_PIN);
    // temp computation moved to Controller.py
    // send v to Controller through MQTT

    // pir presence timeout moved to Controller.py

    Serial.print("PIR presence: "); Serial.print(pir_presence);
    Serial.print("\tMicrophone presence: "); Serial.println(microphone_presence);

    // heating system and air conditioning logic moved to Controller.py
    // retreive data on MQTT

    // analogWrite on pin has to be moved in MQTT callback

    if (Serial.available()) {
        change_max_min();
    }
    
    delay(1000);
}


void pir_presence_isr() {
    pir_presence = 1;
    // update pir value on mqtt
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

    microphone_presence = (sum >= n_sound_events) ? 1:0;

    // TODO: send microphone_presence val on MQTT

    delay(sound_interval / BUFFER_SIZE_SAMPLES_CNT);
}


void loop_refresh_display() {

    lcd.home();
    lcd.clear();

    if (display_state) {
        sprintf(lcd_buffer[0], "T:%.1lf Pres:%d", temperature, presence);
        sprintf(lcd_buffer[1], "AC:%d%% HT:%d%%", (int) (ac_percentage * 100), (int) (ht_percentage * 100));
    }
    else {
        if (presence) {
            sprintf(lcd_buffer[0], "AC m:%.1f M:%.1f\%", min_ac_presence, max_ac_presence);
            sprintf(lcd_buffer[1], "HT m:%.1f M:%.1f\%", min_h_presence, max_h_presence);
        }
        else {
            sprintf(lcd_buffer[0], "AC m:%.1f M:%.1f\%", min_ac_absence, max_ac_absence);
            sprintf(lcd_buffer[1], "HT m:%.1f M:%.1f\%", min_h_absence, max_h_absence);
        }
    }

    display_state = 1 - display_state;

    lcd.setCursor(0, 0);
    lcd.print(lcd_buffer[0]);
    lcd.setCursor(0, 1);
    lcd.print(lcd_buffer[1]);

    delay(3000);
}


void change_max_min() {
    char a_h, M_m, p_a;
    float value;
    String str;
    
    str = Serial.readString();
    str.trim();

    if (sscanf(str.c_str(), "%c %c %c: %f", &a_h, &M_m, &p_a, &value) == 4) {
        if (a_h == 'a') {
            if (M_m == 'M') {
                if (p_a == 'p') {
                    max_ac_presence = value;
                } else if (p_a == 'a') {
                    max_ac_absence = value;
                }
            } else if (M_m == 'm') {
                if (p_a == 'p') {
                    min_ac_presence = value;
                } else if (p_a == 'a') {
                    min_ac_absence = value;
                }
            }
        } else if (a_h == 'h') {
            if (M_m == 'M') {
                if (p_a == 'p') {
                    max_h_presence = value;
                } else if (p_a == 'a') {
                    max_h_absence = value;
                }
            } else if (M_m == 'm') {
                if (p_a == 'p') {
                    min_h_presence = value;
                } else if (p_a == 'a') {
                    min_h_absence = value;
                }
            }
        }
    }
}


/*
 * CONNECTIVITY FUNCTIONS
 */

void callback(char *topic, byte *payload, unsigned int length) {
    Serial.println(String("Message received on topic: ") + topic);

    return;  
}


void connectivity_setup() {
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
        Serial.println("GET request...");

        http_client.get("/");
        return_code = http_client.responseStatusCode();

        Serial.println("Response code: " + return_code);
    }

    body = http_client.responseBody();

    DeserializationError err = deserializeJson(doc_rec_cat, body.c_str());

    if (err) {
        Serial.print("deserializeJson() failed with code: ");
        Serial.println(err.c_str());
    }

    const char *tmp = doc_rec_cat["ep"]["m"]["hn"][0]["v"];
    broker_address = String(tmp);
    broker_port = doc_rec_cat["ep"]["m"]["pt"][0]["v"];

    const char *tmp_ = doc_rec_cat["ep"]["m"]["bt"][0]["v"];
    catalog_base_topic = String(tmp) + String("/devices");

    Serial.print("[DEBUG] Broker info: "); Serial.print(broker_address); Serial.print(":"); Serial.println(broker_port);
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


void refresh_catalog_subscription() {
    String output;

    if (mqtt_client.state() != MQTT_CONNECTED) {
        mqtt_reconnect();
    }

    // Create body
    doc_snd_cat_sub.clear();
    doc_snd_cat_sub["id"] = device_id;
    doc_snd_cat_sub["ep"]["m"]["p"][0]["v"] = base_topic + String("/temp");
    doc_snd_cat_sub["ep"]["m"]["s"][0]["v"] = base_topic + String("/led");
    doc_snd_cat_sub["in"]["r"][0]["n"] = "pub/temp";
    doc_snd_cat_sub["in"]["r"][1]["n"] = "sub/led";

    serializeJson(doc_snd_cat_sub, output);

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

    doc_snd_sen_ml.clear();
    doc_snd_sen_ml["bn"] = device_id;
    doc_snd_sen_ml["e"][0]["n"] = dev;
    doc_snd_sen_ml["e"][0]["t"] = int(millis()/1000);
    doc_snd_sen_ml["e"][0]["v"] = val;
    doc_snd_sen_ml["e"][0]["u"] = unit;

    serializeJson(doc_snd_sen_ml, output);
    return output;
}