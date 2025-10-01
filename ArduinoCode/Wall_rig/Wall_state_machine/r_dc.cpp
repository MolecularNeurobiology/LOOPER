#include <Arduino.h>
#include "r_dc.h"

dc_motor_info dcmotor = {
  8,        // enable
  0,        // enable_duty
  0,        // in2
  0,        // in1
  0,        // potential
  0,        // potential_value
  0,        // encoder
  0,        // encoder_last_state
  0,        // encoder_now_state
  0,        // encoder_pulse
  0.0,      // rpm
  5000,        // rpm_period
  0,        // current_time;
  0,      // prev_time;
};

dc_valve_info v1 = {
  22,        // enable
  1000,     // period
  0         //prev_time
};

DCState dcstate = DC_off;
Valve1State v1state = Valve1_off;

void calibration_on() {
  analogWrite(dcmotor.enable, 255);
}

void calibration_off() {
  analogWrite(dcmotor.enable, 0);
}

void valve1_on() {
  digitalWrite(v1.enable, HIGH);
}

void valve1_off() {
  digitalWrite(v1.enable, LOW);
}

void calibration_setup() {
  pinMode(dcmotor.enable, OUTPUT);
  pinMode(v1.enable, OUTPUT);
  //pinMode(dcmotor.in1, OUTPUT);
  //pinMode(dcmotor.in2, OUTPUT);
  //pinMode(dcmotor.encoder, INPUT);

  dcmotor.prev_time = millis();
    while (millis() - dcmotor.prev_time < 3000) {
      analogWrite(dcmotor.enable, 255);
    }
  analogWrite(dcmotor.enable, 0);
}