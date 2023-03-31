#include <LiquidCrystal_PCF8574.h>
#include <Wire.h>

#define TEMP_PIN A0

const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;

double r, t;

LiquidCrystal_PCF8574 lcd(0x27);

char lcdDisplay[2][20];

void setup() {
  Serial.begin(9600);
  while (!Serial);
  Serial.println("Lab 1.5 starting");
  
  Wire.begin();
  Wire.beginTransmission(0x27);

  lcd.begin(20, 4);
  lcd.setBacklight(255);

  pinMode(TEMP_PIN, INPUT);
}

void loop() {
  char lcdbuf[21];
  double v = (double)analogRead(TEMP_PIN);

  r = (1023.0 / v - 1.0) * (double)R1;
  t = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;

  lcd.home();
  lcd.clear();
  lcd.setCursor(0,0);

  sprintf(lcdbuf, "Temperature: %.2f\0", (float)t);
  lcd.print(lcdbuf);

  Serial.print("Temperature: ");
  Serial.println(t);

  delay(5000);
}
