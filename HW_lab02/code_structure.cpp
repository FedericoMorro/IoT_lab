#include <LiquidCrystal_PCF8574.h>
#include <Wire.h>

#define FAN_PIN     0
#define RED_LED_PIN 0
#define PIR_PIN     0

int temperature;
uint16_t 

LiquidCrystal_PCF8574 lcd(0x20);
char lcd_buffer[21][2];

void setup() {
    Serial.begin(9600);
    while (!Serial);
    Serial.println("Lab 2 starting");

    lcd.begin(16, 2);
    lcd.setBacklight(255);
}


void loop() {

    lcd.home();
    lcd.clear();
    sprintf(lcd_buffer[0], "T:%.\f Pres:%d", 0.0, 0);
    sprintf(lcd_buffer[1], "AC:%d\% HT:$ì%d\%", 0, 0);
    //sprintf(lcd_buffer[0], "AC m:%.1f M:%.1f\%", 0.0, 0.0);
    //sprintf(lcd_buffer[1], "HT m:%.1f M:%.1f\%", 0.0, 0.0);
    lcd.print(lcd_buffer);

}