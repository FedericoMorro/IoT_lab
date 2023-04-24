#include <PDM.h>
#include <LiquidCrystal_PCF8574.h>
#include <Wire.h>
#include <Scheduler.h>


#define TEMPERATURE_PIN A0

#define FAN_PIN       4
#define RED_LED_PIN   2
#define GREEN_LED_PIN 21
#define PIR_PIN       7


const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;
double v, r, temperature;

uint8_t air_conditioning_intensity;
float ac_percentage;
float min_ac_absence = 20;
float max_ac_absence = 25;
float min_ac_presence = 25;//20;
float max_ac_presence = 30;
uint8_t ac_pwm_value(float temp, float min, float max);

const uint8_t min_fan_speed = 124;    // min pwm to turn on the fan
const uint8_t max_fan_speed = 255;

uint8_t heating_intensity;
float ht_percentage;
float min_h_absence = 20;//10;
float max_h_absence = 25;//15;
float min_h_presence = 25;//10;
float max_h_presence = 30;//20;
uint8_t h_pwm_value(float temp, float min, float max);

const uint8_t min_led_intensity = 0;
const uint8_t max_led_intensity = 255;

uint8_t presence;

uint8_t pir_presence;
const int pir_timeout = 10 * 1000;      //30 * 60 * 1000;
int pir_time;
void pir_presence_isr();

uint8_t sound_presence;
const uint8_t n_sound_events = 2;   // tbc
const int sound_threshold = 100;    // tbc
const int sound_interval = 20 * 1000;   //60 * 60 * 1000;
short sample_buffer[256];      // buffer to read sample into, each sample is 16-bit
void on_PDM_data();
int n_samples_read;

LiquidCrystal_PCF8574 lcd(0x20);
char lcd_buffer[2][21];
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
        Serial.println("Failed to start PDM");
        while (1);
    }

    Wire.begin();
    Wire.beginTransmission(0x27);
    lcd.begin(16, 2);
    lcd.setBacklight(255);

    air_conditioning_intensity = 0;
    heating_intensity = 0;

    presence = 0;

    pir_presence = 0;
    
    sound_presence = 0;
    n_samples_presence = 0;

    display_state = 1;
    Scheduler.startLoop(refresh_display);
}


void loop() {
    v = (double) analogRead(TEMPERATURE_PIN);
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

    if (Serial.available()) {
        char a_h, M_m, p_a;
        float value;
        String str = Serial.readString();
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
    
    delay(100);
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
    n_samples_read += bytes_available / 2;
}


uint8_t ac_pwm_value(float temp, float min, float max) {
    if (!(temp >= min && temp <= max)) {
        return 0;
    }

    ac_percentage = (temp - min) / (max - min);
    return (uint16_t) (ac_percentage * (max_fan_speed - min_fan_speed) + min_fan_speed);
}


uint8_t h_pwm_value(float temp, float min, float max) {
    if (!(temp >= min && temp <= max)) {
        return 0;
    }

    ht_percentage = (max - temp) / (max - min);
    return (uint16_t) (ht_percentage * (max_led_intensity - min_led_intensity) + min_led_intensity);
}


void refresh_display() {

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