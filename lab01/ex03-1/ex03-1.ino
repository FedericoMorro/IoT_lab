#define R_LED_PIN 2
#define G_LED_PIN 3
#define PIR_PIN   4

volatile int presence = 0;
volatile int cnt = 0;

void setup() {
  //pinMode(R_LED_PIN, OUTPUT);
  //pinMode(G_LED_PIN, OUTPUT);

  pinMode(PIR_PIN, INPUT);

  attachInterrupt(digitalPinToInterrupt(PIR_PIN), check_presence, FALLING);
}

void loop() {
  if (presence) {
    Serial.println(cnt);
    presence--;
  }
}

void check_presence() {
  cnt++;
  presence++;
}