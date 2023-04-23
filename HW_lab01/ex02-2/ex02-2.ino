#include <Scheduler.h>

#define R_LED_PIN 2
#define G_LED_PIN 3

const long R_HALF_PERIOD = 1500L;
const long G_HALF_PERIOD = 3500L;

volatile int r_led_status = LOW;
volatile int g_led_status = LOW;

void setup() {
  Serial.begin(9600);
  while (!Serial);
  Serial.println("Lab 1.2 Starting");

  pinMode(R_LED_PIN, OUTPUT);
  pinMode(G_LED_PIN, OUTPUT);

  Scheduler.startLoop(loopR);
  Scheduler.startLoop(loopG);
}

void loop() {
  if (Serial.available() > 0)
    serial_print_status();
  yield();
}


void serial_print_status() {
  int in_byte = Serial.read();

  switch (in_byte) {      
    case 'R':
      Serial.print("Red led status: ");
      Serial.println(r_led_status);
      break;

    case 'G':
      Serial.print("Green led status: ");
      Serial.println(g_led_status);
      break;

    default:
      Serial.println("Wrong command (insert R or G)");
      break;
  }
}


void loopR() {
  digitalWrite(R_LED_PIN, r_led_status);
  r_led_status = !r_led_status;
  delay(R_HALF_PERIOD);
}


void loopG() {
  digitalWrite(G_LED_PIN, g_led_status);
  g_led_status = !g_led_status;
  delay(G_HALF_PERIOD);
}