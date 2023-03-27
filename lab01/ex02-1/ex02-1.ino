#include <MBED_RPi_Pico_TimerInterrupt.h>

#define R_LED_PIN 2
#define G_LED_PIN 3

const long R_HALF_PERIOD = 1500L;
const long G_HALF_PERIOD = 3500L;

volatile int r_led_status = LOW;
volatile int g_led_status = LOW;

MBED_RPI_PICO_Timer ITimer1(1);

void setup() {
  Serial.begin(9600);
  while (!Serial);
  Serial.println("Lab 1.2 Starting");

  pinMode(R_LED_PIN, OUTPUT);
  pinMode(G_LED_PIN, OUTPUT);

  ITimer1.setInterval(G_HALF_PERIOD * 1000, blink_green);
}

void loop() {
  digitalWrite(R_LED_PIN, r_led_status);
  r_led_status = !r_led_status;
  delay(R_HALF_PERIOD);

  if (Serial.available() > 0)
    serial_print_status();
}

void blink_green(uint alarm_num) {
  TIMER_ISR_START(alarm_num);

  digitalWrite(G_LED_PIN, g_led_status);
  g_led_status = !g_led_status;

  TIMER_ISR_END(alarm_num);
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
