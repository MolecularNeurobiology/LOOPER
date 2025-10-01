#ifndef R_STEPPER_H
#define R_STEPPER_H
#include <AS5600.h>


struct stepper1Info {
  // goes to each syrange
  int pull_1;
  int dir_1;
  int enablePin;
  int speed; // Adjustable speed for Stepper1
  int maxspeed; // Adjustable maxspeed for Stepper2
  int acceleration; // Adjustable acceleration for Stepper2
  int targetpos; 
  int pause_period;
  unsigned long current_time;//calibrating motor timer
  unsigned long prev_time;//calibrating motor previous timer
};

enum Stepper1State {
  S1IDLE,
  MOVING_OUT,
  S1_S2_F,
  S1_Pause,
  S1_S2_B,
  MOVING_HOME
};

struct stepper2Info {
  // goes back and forth
  int pull_2;
  int dir_2;
  int enablePin;
  int speed; // Adjustable speed for Stepper2
  int maxspeed; // Adjustable maxspeed for Stepper2
  int acceleration; // Adjustable acceleration for Stepper2
};

enum Stepper2State {
  S2IDLE,
  MOVING_F,
  MOVING_B
};

struct sensorPins {
  int Sensor_home;
  int Sensor_f;
  int Sensor_b;
};

void move_f();
void move_b();
void move_pos(int pos);
void move_0();
void stopMotor1();
void stopMotor2();
void setup_stepper();
void AS5600_setup();
void AS5600_reset();
float AS5600_increment();

extern stepper1Info stepper1;
extern stepper2Info stepper2;
extern Stepper2State stepper2state;
extern Stepper1State stepper1state;

extern sensorPins sensors;
extern AS5600 encoder;
extern uint16_t prevRaw;
extern float totalAngle;

#endif