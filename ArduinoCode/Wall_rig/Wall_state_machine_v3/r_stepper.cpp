#include <Arduino.h>
#include <AccelStepper.h> 
#include "r_stepper.h"
#include <Wire.h>
#include <AS5600.h>

AS5600 encoder;
uint16_t prevRaw = 0;
float totalAngle = 0.0;

stepper1Info stepper1 = {
  5,     //pull_1
  6,    //dir_1
  7,      //enablePin
  300,  // Adjustable speed for Stepper2
  500, // maxspeed
  200,  // acceleration
  0,  //targetPos = posiotion[cmd.index2-1]
  0,        // rpm_period = cmd.index3  for <P,#,n> 
  0,        // current_time;
  0,      // prev_time;
  0,      //standby   for <S,0,0>
  0,      //target_index  for <P,#,n>0>, to print("Finished:On Position #, Prefilled for #s")
  0,      //anoxic    for <A,#,#>
  0,      //room    for <R,0,0>
};

stepper2Info stepper2 = {
  2,    //pull_2
  3,    //dir_2
  4,    //enablePin
  300,  // Adjustable speed for Stepper2
  500, // maxspeed
  200,  // acceleration
};

sensorPins sensors = {
  10,
  11,
  12,
};

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

Valve_info valve = {
  22,        // enable
  24,
  22,
  24,
  0,
  1000,     // period
  0         //prev_time
};

extern AccelStepper stepper1Motor; // Declare the stepper motor instance from main file
extern AccelStepper stepper2Motor; // Declare the stepper motor instance from main file
Stepper2State stepper2state = S2_IDLE;
Stepper1State stepper1state = S1_IDLE;

DCState dcstate = DC_off;
ValveState  valvestate = Valve_off;

void stopMotor2() {
  digitalWrite(stepper2.enablePin, HIGH);  // Disable motor
  stepper2Motor.setSpeed(0);
}

void stopMotor1() {
  digitalWrite(stepper1.enablePin, HIGH);  // Disable motor
  stepper1Motor.setSpeed(0);
}

void move_f() {
  digitalWrite(stepper2.enablePin, LOW);
  stepper2Motor.setSpeed(-stepper2.speed);
}

void move_b() {
  digitalWrite(stepper2.enablePin, LOW);
  stepper2Motor.setSpeed(stepper2.speed);
}

// Function to move stepper1 to a specified position
void move_pos(int pos)  {
  digitalWrite(stepper1.enablePin, LOW);
  stepper1Motor.moveTo(pos);
  stepper1Motor.setSpeed(stepper1.speed);
}

void move_0() {
  digitalWrite(stepper1.enablePin, LOW);
  stepper1Motor.setSpeed(-stepper1.speed); // Reverse direction for homing
}

void setup_stepper(){
  // Initialize stepper motor enable pins
  pinMode(stepper1.enablePin, OUTPUT);
  pinMode(stepper2.enablePin, OUTPUT);

  // Disable steppers initially
  digitalWrite(stepper1.enablePin, HIGH);
  digitalWrite(stepper2.enablePin, HIGH);
  
  // Initialize sensor pins
  pinMode(sensors.Sensor_home, INPUT);
  pinMode(sensors.Sensor_f, INPUT);
  pinMode(sensors.Sensor_b, INPUT);

  // Configure stepper motors
  stepper1Motor.setMaxSpeed(stepper1.maxspeed);
  stepper1Motor.setAcceleration(stepper1.acceleration);
  stepper2Motor.setMaxSpeed(stepper2.maxspeed);
  stepper2Motor.setAcceleration(stepper2.acceleration);
  
    // Initial setup sequence
  if (digitalRead(sensors.Sensor_f) == LOW || digitalRead(sensors.Sensor_b) == LOW) {
    // Enable stepper2
    digitalWrite(stepper2.enablePin, LOW);

    // Move stepper2 clockwise until Sensor_b is high
    while (digitalRead(sensors.Sensor_b) == LOW) {
      stepper2Motor.setSpeed(200);
      stepper2Motor.runSpeed();
    }

    // Move stepper1 clockwise until Sensor_home is high
    digitalWrite(stepper1.enablePin, LOW);
    stepper1Motor.setSpeed(-300); // Reverse direction for homing
    while (digitalRead(sensors.Sensor_home) == LOW) {
      stepper1Motor.runSpeed();
    }
    stepper1Motor.setCurrentPosition(0); // Set home position
    digitalWrite(stepper1.enablePin, HIGH);

    // Move stepper2 counterclockwise until Sensor_f is high
    while (digitalRead(sensors.Sensor_f) == LOW) {
      stepper2Motor.setSpeed(-200);
      stepper2Motor.runSpeed();
    }

    // Move stepper2 clockwise again until Sensor_b is high
    while (digitalRead(sensors.Sensor_b) == LOW) {
      stepper2Motor.setSpeed(200);
      stepper2Motor.runSpeed();
    }

    digitalWrite(stepper2.enablePin, HIGH); // Disable stepper2
  }
}

void AS5600_setup() {
  Wire.begin();
  encoder.begin();

  if (!encoder.isConnected()) {
    //Serial.println("AS5600 not connected!");
    while (1);
  }

  prevRaw = encoder.readAngle();
  totalAngle = 0.0;

  //Serial.println("AS5600 setup complete");
}

void AS5600_reset() {
  prevRaw = encoder.readAngle();
  totalAngle = 0.0;
}

float AS5600_increment() {
  uint16_t raw = encoder.readAngle();
  int delta = raw - prevRaw;

  if (delta > 2048) delta -= 4096;
  else if (delta < -2048) delta += 4096;

  float deltaDeg = delta * 360.0 / 4096.0;
  totalAngle += deltaDeg;

  prevRaw = raw;
  return totalAngle;
}

void dc_on() {
  analogWrite(dcmotor.enable, 255);
}

void dc_off() {
  analogWrite(dcmotor.enable, 0);
}

void valve_open(int valve_num) {
  switch (valve_num) {
    case 1:
      digitalWrite(valve.v1_enable, HIGH);
      break;
    case 2:
      digitalWrite(valve.v2_enable, HIGH);
      break;
    case 3:
      digitalWrite(valve.v3_enable, HIGH);
      break;
    case 4:
      digitalWrite(valve.v4_enable, HIGH);
      break;
    default:
      break;
  }
}

void valve_close(int valve_num) {
  switch (valve_num) {
    case 1:
      digitalWrite(valve.v1_enable, LOW);
      break;
    case 2:
      digitalWrite(valve.v2_enable, LOW);
      break;
    case 3:
      digitalWrite(valve.v3_enable, LOW);
      break;
    case 4:
      digitalWrite(valve.v4_enable, LOW);
      break;
    default:
      break;
  }
}

void valve_close_all() {

  digitalWrite(valve.v1_enable, LOW);
  digitalWrite(valve.v2_enable, LOW);
  digitalWrite(valve.v3_enable, LOW);
  digitalWrite(valve.v4_enable, LOW);
}

void dc_setup() {
  pinMode(dcmotor.enable, OUTPUT);
  pinMode(valve.v1_enable, OUTPUT);
  pinMode(valve.v2_enable, OUTPUT);
  //pinMode(dcmotor.in1, OUTPUT);
  //pinMode(dcmotor.in2, OUTPUT);
  //pinMode(dcmotor.encoder, INPUT);

  //dcmotor.prev_time = millis();
  //  while (millis() - dcmotor.prev_time < 3000) {
  //    analogWrite(dcmotor.enable, 255);
  //  }
  analogWrite(dcmotor.enable, 0);
}
