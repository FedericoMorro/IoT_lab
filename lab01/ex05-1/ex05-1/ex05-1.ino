#define TEMP_PIN A0

const int B = 4275, T0 = 25;
const long R0 = 100000, R1 = 100000;
const double TK = 273.15;

double r, t;

void setup() {
  Serial.begin(9600);
  while (!Serial);
  Serial.println("Lab 1.5 starting");
  
  pinMode(TEMP_PIN, INPUT);
}

void loop() {
  double v = (double)analogRead(TEMP_PIN);

  r = (1023.0 / v - 1.0) * (double)R1;
  t = 1.0 / ( (log(r / (double)R0) / (double)B) + (1.0 / ((double)T0 + TK))) - TK;

  Serial.print("Temperature: ");
  Serial.println(t);

  delay(5000);
}
