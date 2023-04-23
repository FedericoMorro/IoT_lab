#define FAN_PIN 4

float current_speed;
const int max_pwm = 255;
const int min_pwm = 0;
const float step = 0.1;

void setup() {
  Serial.begin(9600);
  while (!Serial);
  Serial.println("Lab 1.4 starting");

  current_speed = 0;

  pinMode(FAN_PIN, OUTPUT);
  analogWrite(FAN_PIN, (int) current_speed);
}

void loop() {
  
  if (Serial.available()) {
    int c;
    c = Serial.read();

    switch (c) {
      
      case '+':
        if (current_speed >= max_pwm) {
          Serial.println("Maximum speed reached");
          break;
        }
        current_speed += step * (float) max_pwm;
        Serial.print("Increasing speed: ");
        Serial.println(current_speed);
        break;

      case '-':
        if (current_speed <= min_pwm) {
          Serial.println("Minimum speed reached");
          break;
        }
        current_speed -= step * (float) max_pwm;
        Serial.print("Decreasing speed: ");
        Serial.println(current_speed);        
        break;
      
      default:
        Serial.println("Unknown command");
        break;
    }
    analogWrite(FAN_PIN, (int) current_speed);
  }

  delay(10);
}
