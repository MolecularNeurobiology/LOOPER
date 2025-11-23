#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "r_display.h"

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// Store latest text for each line
String line0Text = "";
String line1Text = "";
String line2Text = "";
String prev0 = "", prev1 = "", prev2 = "";

void setupDisplay() {
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;); // Don't proceed, loop forever
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

String stepper1StateToString(Stepper1State state) {
  switch (state) {
    case S1IDLE: return "S1_IDLE";
    case MOVING_OUT: return "S1_OUT";
    case S1_Pause: return "S1_PAUSE";
    case S1_S2_F: return "S1_S2_F";
    case S1_S2_B: return "S1_S2_B";
    case MOVING_HOME: return "S1_HOME";
    default: return "S1_UNKNOWN";
  }
}

int stepper1StateToNumber(Stepper1State state) {
  switch (state) {
    case S1IDLE:     return 0;
    case MOVING_OUT: return 1;
    case S1_S2_F:    return 2;
    case S1_Pause:   return 3;
    case S1_S2_B:    return 4;
    case MOVING_HOME:return 5;
    default:         return -1;  // for safety
  }
}

String stepper2StateToString(Stepper2State state) {
  switch (state) {
    case S2IDLE: return "S2_IDLE";
    case MOVING_F: return "S2_FWD";
    case MOVING_B: return "S2_BWD";
    default: return "S2_UNKNOWN";
  }
}

int stepper2StateToNumber(Stepper2State state) {
  switch (state) {
    case S2IDLE:     return 0;
    case MOVING_F: return 1;
    case MOVING_B:    return 2;
    default:         return -1;  // for safety
  }
}

int DCStateToNumber(DCState state) {
  switch (state) {
    case DC_off:     return 0;
    case DC_on:      return 1;
    default:         return -1;  // for safety
  }
}

int Valve1StateToNumber(Valve1State state) {
  switch (state) {
    case Valve1_off:     return 0;
    case Valve1_on:      return 1;
    case Valve1_hold:      return 2;
    default:         return -1;  // for safety
  }
}
