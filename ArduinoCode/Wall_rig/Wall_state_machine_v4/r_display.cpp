#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "r_display.h"

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &SPI, OLED_DC, OLED_RESET, OLED_CS);

// Store latest text for each line
String line0Text = "";
String line1Text = "";
String line2Text = "";
String prev0 = "", prev1 = "", prev2 = "";

void setupDisplay() {
  if (!display.begin(SSD1306_SWITCHCAPVCC)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.display();
}

void displayLine0(const String &text) {
  display.fillRect(0, 0, 128, 10, BLACK);
  display.setCursor(0, 0);
  display.println(text);
  display.display();
}

void setLine0(const String &text) { line0Text = text; }
void setLine1(const String &text) { line1Text = text; }
void setLine2(const String &text) { line2Text = text; }

void update_motor_state(){
  setLine1( stepper1StateToString(stepper1state)+ "," + stepper2StateToString(stepper2state));
}

void updateDisplay() {
  bool changed = false;

  if (line0Text != prev0 || line1Text != prev1 || line2Text != prev2) {
    changed = true;
    display.clearDisplay();

    display.setCursor(0, 0);
    display.println(line0Text);

    display.setCursor(0, 10);
    display.println(line1Text);

    display.setCursor(0, 20);
    display.println(line2Text);

    display.display();

    prev0 = line0Text;
    prev1 = line1Text;
    prev2 = line2Text;
  }
}


int stepper1StateToNumber(Stepper1State state) {
  switch (state) {
    case S1_IDLE: return 0;
    case S1_HOME: return 1;
    case S1_OUT:  return 2;
    default:      return -1;
  }
}

int stepper2StateToNumber(Stepper2State state) {
  switch (state) {
    case S2_IDLE:     return 0;
    case S2_F:        return 1;
    case S2_B:        return 2;
    default:          return -1;  // for safety
  }
}

int DCStateToNumber(DCState state) {
  switch (state) {
    case DC_off:     return 0;
    case DC_on:      return 1;
    case DC_hold:      return 2;
    default:         return -1;  // for safety
  }
}

int ValveStateToNumber(ValveState state) {
  switch (state) {
    case Valve_off:     return 0;
    case Valve_on:      return 1;
    case Valve_hold:      return 2;
    default:         return -1;  // for safety
  }
}
