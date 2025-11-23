#ifndef R_DC_H
#define R_DC_H

struct dc_motor_info {
  int enable;
  int enable_duty;
  int in2;
  int in1;
  int potential;
  int potential_value;
  int encoder;
  int encoder_last_state;
  int encoder_now_state;
  volatile long encoder_pulse;
  float rpm;
  int rpm_period;
  unsigned long current_time;//calibrating motor timer
  unsigned long prev_time;//calibrating motor previous timer
};

enum DCState {
  DC_on,
  DC_off
};


struct dc_valve_info {
  int enable;  
  int valve_period;      
  unsigned long prev_time;
};

enum Valve1State {
  Valve1_on,
  Valve1_off,
  Valve1_hold
};

extern dc_motor_info dcmotor;
extern dc_valve_info v1;
extern DCState dcstate;
extern Valve1State v1state;

void calibration_on();
void calibration_off();
void calibration_setup();
void valve1_on();
void valve1_off();

#endif