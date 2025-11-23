#ifndef R_ACTUATOR_H
#define R_ACTUATOR_H
#include <AS5600.h>
#include <Adafruit_MAX31855.h>
#include <PID_v1.h>

//------------------------ stepper ----------------------------
//------------------------ stepper ----------------------------

struct Stepper1Config  {
  // goes to each syrange
  const int pull_1;
  const int dir_1;
  const int enablePin;
  int speed; // Adjustable speed for Stepper1
  int maxspeed; // Adjustable maxspeed for Stepper2
  int acceleration; // Adjustable acceleration for Stepper2
  int targetpos; 
  unsigned long pause_period;
  unsigned long current_time;//calibrating motor timer
  unsigned long prev_time;//calibrating motor previous timer
  bool isStandby; //isStandby   for <S,0,0>
  int target_index;  //target_index  for <P,#,n>0>, to print("Finished:On Position #, Prefilled for #s")
  bool isAnoxic; //isAnoxic    for <A,#,#>
  bool isRoomTemp; //isRoomTemp    for <R,0,0>

}; 

enum Stepper1State {
  S1_IDLE,
  S1_HOME,
  S1_OUT,
};

struct Stepper2Config  {
  // goes back and forth
  const int pull_2;
  const int dir_2;
  const int enablePin;
  int speed; // Adjustable speed for Stepper2
  int maxspeed; // Adjustable maxspeed for Stepper2
  int acceleration; // Adjustable acceleration for Stepper2
};

enum Stepper2State {
  S2_IDLE,
  S2_F,
  S2_B,
};

//------------------------ sensor ----------------------------
//------------------------ sensor ----------------------------

struct SensorPins {
  const int Sensor_home;
  const int Sensor_f;
  const int Sensor_b;
};

//------------------------ DC motor ----------------------------
//------------------------ DC motor ----------------------------

struct DcMotorConfig  {
  const int enable;
  int enable_duty;
  const int in2;
  const int in1;
  int potential;
  int potential_value;
  int encoder;
  int encoder_last_state;
  int encoder_now_state;
  volatile long encoder_pulse;
  float rpm;
  unsigned long rpm_period;
  unsigned long current_time;//calibrating motor timer
  unsigned long prev_time;//calibrating motor previous timer
};

enum DcMotorState  {
  DC_on,
  DC_off,
  DC_hold,
};

//------------------------ Valve ----------------------------
//------------------------ Valve ----------------------------

struct ValveConfig  {
  const int v1_enable;  
  const int v2_enable;
  const int v3_enable;
  const int v4_enable;
  int v_number;
  unsigned long valve_period;      
  unsigned long prev_time;
};

enum ValveState {
  Valve_on,
  Valve_off,
  Valve_off_all,
  Valve_hold,
};

//------------------------ Heater ----------------------------
//------------------------ Heater ----------------------------


struct HeaterConfig  {
  const int enable;
  const int MAX31855_CS;
  double TC;
  double TC_pre;
  double TC_filter;  
  int basepwm;
  double PWM; 
  const int led_pin;
  bool ledState;
  int ledCounter; 
};

struct HeaterPIDConfig {
  double setpoint;
  double output;
  //double error;
  double kp;
  double ki;
  double kd;
  unsigned long PID_period;
  unsigned long prev_time;
};

enum HeaterState {
  Heater_on,
  Heater_off,
  Heater_auto,
};

//------------------------ Encoder ----------------------------
//------------------------ Encoder ----------------------------
struct AS5600Config  {
  uint16_t prevRaw;
  float totalAngle;
};

//------------------------ Filters  ----------------------------
//------------------------ Filters  ----------------------------
struct MovingAverage {
  static const uint8_t window = 10;   // size of the MA window
  double buf[window];                // circular buffer
  uint8_t index;                       // write index [0..window-1]
  uint8_t count;                     // number of valid samples (<= window)
  double sum;                        // running sum of buf values

  void reset();                      // zero state
  double push(double sample);        // add sample, return average
};


//------------------------ Functions  ----------------------------
//------------------------ Functions  ----------------------------
void move_f();
void move_b();
void move_pos(int pos);
void move_0();
void stopMotor1();
void stopMotor2();
void setup_stepper();
void dc_on();
void dc_off();
void dc_setup();
void valve_open(int valve_num);
void valve_close(int valve_num);
void valve_close_all();
void heater_on();
void heater_off();
void heater_auto();
void heater_setup();
double  heater_read();
void as5600_setup();
void as5600_reset();
float as5600_increment();

//------------------------ Globals   ----------------------------
//------------------------ Globals   ----------------------------
extern Stepper1Config  stepper1;
extern Stepper2Config  stepper2;
extern Stepper2State stepper2state;
extern Stepper1State stepper1state;
extern SensorPins sensors;
extern DcMotorConfig  dcmotor;
extern DcMotorState  dcstate;
extern ValveConfig  valve;
extern ValveState valvestate;
extern HeaterConfig  heater;
extern HeaterPIDConfig heaterpid;
extern HeaterState  heaterstate;
extern AS5600Config as5600;
extern AS5600 encoder;
extern MovingAverage tcFilter;


#endif