#ifndef R_DISPLAY_H
#define R_DISPLAY_H
#include "r_stepper.h"
#include "r_pcc.h"

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET    -1
#define SCREEN_ADDRESS 0x3C

extern Adafruit_SSD1306 display;
extern String line0Text;
extern String line1Text;
extern String line2Text;

String stepper1StateToString(Stepper1State state);
String stepper2StateToString(Stepper2State state);
int stepper1StateToNumber(Stepper1State state);
int stepper2StateToNumber(Stepper2State state);
int DCStateToNumber(DCState state);
int ValveStateToNumber(ValveState state);

void setupDisplay();
void displayLine0(const String &text);
void setLine0(const String &text);
void setLine1(const String &text);
void setLine2(const String &text);
void update_motor_state();
void updateDisplay();

#endif