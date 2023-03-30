#define R_LED_PIN 2
#define G_LED_PIN 3
#define PIR_PIN   4

volatine int status = 0;
volatile int cnt = 0;

void setup() {
  //pinMode(R_LED_PIN, OUTPUT);
  pinMode(G_LED_PIN, OUTPUT);

  pinMode(PIR_PIN, INPUT);

  attachInterrupt(digitalPinToInterrupt(PIR_PIN), check_presence, CHANGE);
}

void loop() {
  Serial.print("Total people count:");
  Serial.println(cnt);
  delay(30000);
}

void check_presence() {
  if (!status) {
    status++;
    cnt++;
    digitalWrite(G_LED_PIN, HIGH);
  } else {
    status--;
    digitalWrite(G_LED_PIN, LOW);
  }
}