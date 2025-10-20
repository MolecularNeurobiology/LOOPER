

const unsigned SAMPLE_MS = 2;   // ~500 samples/sec

void setup() {
  Serial.begin(9600);
  pinMode(10, INPUT);
  pinMode(11, INPUT);
  pinMode(12, INPUT);
}

void loop() {
  static unsigned long last = 0;
  unsigned long now = millis();
  if (now - last >= SAMPLE_MS) {
    last = now;
    int level1 = digitalRead(10);  // 0=LOW, 1=HIGH
    int level2 = digitalRead(11);  // 0=LOW, 1=HIGH
    int level3 = digitalRead(12);  // 0=LOW, 1=HIGH
        
        
    Serial.print(level1);         // one value per line for Serial Plotter
    Serial.print(",");         // one value per line for Serial Plotter
    Serial.print(level2);         // one value per line for Serial Plotter
    Serial.print(",");
    Serial.println(level3);         // one value per line for Serial Plotter
  }
}
