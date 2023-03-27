#include <Scheduler.h>

const int RLED_PIN = 2;
const int GLED_PIN = 3;

const long R_HALF_PERIOD = 1500L;
const long G_HALF_PERIOD = 3500L;

int redLedState = 0;
int greenLedState = 0;

void setup() {
  // put your setup code here, to run once:
  pinMode(RLED_PIN, OUTPUT);
  pinMode(GLED_PIN, OUTPUT);
  Scheduler.startLoop(loop2);
}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(RLED_PIN, redLedState);
  redLedState = !redLedState;
  delay(R_HALF_PERIOD);
}

void loop2() {
  digitalWrite(GLED_PIN, greenLedState);
  greenLedState = !greenLedState;
  delay(G_HALF_PERIOD);
}
