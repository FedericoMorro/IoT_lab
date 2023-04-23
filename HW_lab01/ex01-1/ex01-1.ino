#include <MBED_RPi_Pico_TimerInterrupt.h>

#define R_LED_PIN 2
#define G_LED_PIN 3

const long R_HALF_PERIOD = 1500L;
const long G_HALF_PERIOD = 3500L;

int r_led_state = LOW;
int g_led_state = LOW;

MBED_RPI_PICO_Timer ITimer1(1);

void setup() {
  pinMode(R_LED_PIN, OUTPUT);
  pinMode(G_LED_PIN, OUTPUT);

  ITimer1.setInterval(G_HALF_PERIOD * 1000, blink_green);
}

void loop() {
  digitalWrite(R_LED_PIN, r_led_state);
  r_led_state = !r_led_state;
  delay(R_HALF_PERIOD);
}

void blink_green(uint alarm_num) {
  TIMER_ISR_START(alarm_num);

  digitalWrite(G_LED_PIN, g_led_state);
  g_led_state = !g_led_state;

  TIMER_ISR_END(alarm_num);
}