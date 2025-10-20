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
  bool standby; //standby   for <S,0,0>
  int target_index;  //target_index  for <P,#,n>0>, to print("Finished:On Position #, Prefilled for #s")
  bool anoxic; //anoxic    for <A,#,#>
  bool room; //room    for <R,0,0>

}; 

enum Stepper1State {
  S1_IDLE,
  S1_HOME,
  S1_OUT,
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
  S2_IDLE,
  S2_F,
  S2_B
};

struct sensorPins {
  int Sensor_home;
  int Sensor_f;
  int Sensor_b;
};

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
  DC_off,
  DC_hold
};

struct Valve_info {
  int v1_enable;  
  int v2_enable;
  int v3_enable;
  int v4_enable;
  int valve_period;      
  unsigned long prev_time;
};

enum ValveState {
  Valve_on,
  Valve_off,
  Valve_hold
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
void dc_on();
void dc_off();
void dc_setup();
void valve_on(int valve_num);
void valve_off(int valve_num);

extern stepper1Info stepper1;
extern stepper2Info stepper2;
extern Stepper2State stepper2state;
extern Stepper1State stepper1state;

extern dc_motor_info dcmotor;
extern Valve_info valve;
extern DCState dcstate;
extern ValveState valvestate;

extern sensorPins sensors;
extern AS5600 encoder;
extern uint16_t prevRaw;
extern float totalAngle;



#endif