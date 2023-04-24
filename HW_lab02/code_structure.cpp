#include <PDM.h>
#include <LiquidCrystal_PCF8574.h>
#include <Wire.h>
#include <Scheduler.h>


#define TEMPERATURE_PIN A0

#define FAN_PIN       0
#define RED_LED_PIN   0
#define GREEN_LED_PIN 0
#define PIR_PIN       0


const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;
double r, temperature;

uint8_t air_conditioning_intensity;
float min_ac_absence;
float max_ac_absence;
float min_ac_presence;
float max_ac_presence;
uint8_t ac_pwm_value(float temp, float min, float max);

const uint8_t min_fan_speed = 0;
const uint8_t max_fan_speed = 255;

uint8_t heating_intensity;
float min_h_absence;
float max_h_absence;
float min_h_presence;
float max_h_presence;
uint8_t h_pwm_value(float temp, float min, float max);

const uint8_t min_led_intensity = 0;
const uint8_t max_led_intensity = 255;

uint8_t presence;

uint8_t pir_presence;
const int pir_timeout = 30 * 60 * 1000;
int pir_time;
void pir_presence_isr();

uint8_t sound_presence;
const uint8_t n_sound_events = 0;
const int sound_threshold = 0;
const int sound_interval = 60 * 60 * 1000;
volatile short sample_buffer[256];      // buffer to read sample into, each sample is 16-bit
void on_PDM_data();
int n_samples_read;

LiquidCrystal_PCF8574 lcd(0x20);
char lcd_buffer[21][2];
void refresh_display();
uint8_t display_state;


void setup() {
    Serial.begin(9600);
    while (!Serial);
    Serial.println("Lab 2 starting");

    pinMode(TEMPERATURE_PIN, INPUT);

    pinMode(FAN_PIN, OUTPUT);
    pinMode(RED_LED_PIN, OUTPUT);
    pinMode(GREEN_LED_PIN, OUTPUT);

    pinMode(PIR_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(PIR_PIN), pir_presence_isr, CHANGE);

    PDM.onReceive(on_PDM_data);   // callback function (ISR)
    if (!PDM.begin(1, 16000)) {     // mono, 16 kHz sample frequency
        Serial.pritln("Failed to start PDM");
        while (1);
    }

    lcd.begin(16, 2);
    lcd.setBacklight(255);

    pir_presence = 0;
    sound_presence = 0;
    presence = 0;

    display_state = 1;
    Scheduler.startLoop(refresh_display);
}


void loop() {

    r = (1023.0 / v - 1.0) * (double)R1;
    temperature = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;

    if (pir_presence || sound_presence) {
        presence = 1;
    }
    else {
        presence = 0;
    }

    if (pir_presence && (millis() - pir_time) > pir_timeout) {
        pir_presence = 0;
    }

    if (presence) {
        air_conditioning_intensity = ac_pwm_value(temperature, min_ac_presence, max_ac_presence);
        heating_intensity = h_pwm_value(temperature, min_h_presence, max_h_presence);
    }
    else {
        air_conditioning_intensity = ac_pwm_value(temperature, min_ac_absence, max_ac_absence);
        heating_intensity = h_pwm_value(temperature, min_h_absence, max_h_absence);
    }
    analogWrite(FAN_PIN, air_conditioning_intensity);
    analogWrite(RED_LED_PIN, heating_intensity);
}


void pir_presence_isr() {
    pir_presence = 1;
    pir_time = millis();
}


void on_PDM_data() {
    // query the number of available bytes
    int bytes_available = PDM.available();
    // read into the sample buffer
    PDM.read(sample_buffer, bytes_available);
    // 16-bit, 2 bytes per sample
    n_samples_read = bytes_available / 2;
}


uint8_t ac_pwm_value(float temp, float min, float max) {
    if (!(temp >= min && temp <= max)) {
        return 0;
    }

    return (uint16_t) ((temp - min) / (max - min) * (max_fan_speed - min_fan_speed) + min_fan_speed);
}


uint8_t h_pwm_value(float temp, float min, float max) {
    if (!(temp >= min && temp <= max)) {
        return 0;
    }

    return (uint16_t) ((max - temp) / (max - min) * (max_led_intensity - min_led_intensity) + min_led_intensity);
}


void refresh_display() {

    lcd.home();
    lcd.clear();

    if (display_state) {
        sprintf(lcd_buffer[0], "T:%.1lf Pres:%d", temperature, 0);
        sprintf(lcd_buffer[1], "AC:%d\% HT:$%d\%", air_conditioning_intensity / 255 * 100, heating_intensity / 255 * 100);
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

    lcd.print(lcd_buffer);

    delay(5000);
}