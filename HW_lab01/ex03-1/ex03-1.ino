#define LED_PIN 3
#define PIR_PIN 4

volatile int status = 0;
volatile int cnt = 0;

void setup() {
  Serial.begin(9600);
  while (!Serial);
  Serial.println("Lab 1.3 starting");
  
  pinMode(LED_PIN, OUTPUT);

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
    cnt++;
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
  status = 1 - status;
}