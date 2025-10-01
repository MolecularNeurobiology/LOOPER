#include <AccelStepper.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>

#include "r_stepper.h"
#include "r_display.h"
#include "r_dc.h"

struct CommandIndices {
  String index1;
  int index2;
  int index3;
  bool valid;
};

char cmd_letter;

// Initialize steppers using AccelStepper library
AccelStepper stepper1Motor(AccelStepper::DRIVER, stepper1.pull_1, stepper1.dir_1);
AccelStepper stepper2Motor(AccelStepper::DRIVER, stepper2.pull_2, stepper2.dir_2);

// Non-blocking timing variables
unsigned long lastSensingTime = 0;
unsigned long lastReportTime = 0;
const unsigned long period_sensing = 50;
const unsigned long period_report = 200;
unsigned long currentTime ;

// Position array
int positions[] = {0, 210, 410, 610}; // Positions for Stepper1

void setup() {
  Serial.begin(115200);
  Wire.begin();             // Start the I2C bus
  Wire.setClock(400000);    // Set I2C speed to 400 kHz (Fast Mode)

  // Initialize OLED display
  setupDisplay();

  // Initialize Stepper
  displayLine0("setup_stepper");
  setup_stepper();
  displayLine0("stepper done");

  // Initialize DC motor
  displayLine0("setup_DC");
  calibration_setup();
  displayLine0("DC done");

  // Initialize encoder
  displayLine0("setup_encoder");
  AS5600_setup();
  displayLine0("encoder done");
}


void loop() {
  
  currentTime = millis();
  reportFunction();
  sensingFunction();

  stepper2Motor.runSpeed();
  stepper1Motor.runSpeed();

 CommandIndices cmd = processSerialCommands();

  if (cmd.valid) {
    cmd_letter = cmd.index1.charAt(0);

    setLine0(cmd.index1 + cmd.index2 + cmd.index3);
    //updateDisplay();

    switch (cmd_letter) {
      case 'B':
        stepper2state  = MOVING_B;
        break;

      case 'F':
        stepper2state  = MOVING_F;
        break;

      case 'C':
        if (cmd.index2 > 0 ) {
            dcmotor.rpm_period = cmd.index2;
            dcmotor.prev_time = millis();
            dcstate  = DC_on;
          }
        break;

      case 'V':
        //v1state = (cmd.index3 == 1) ? Valve1_on : (cmd.index3 == 0) ? Valve1_off : v1state;
        //condition ? value_if_true : value_if_false;
        if (cmd.index3 == 1) {
          v1state = Valve1_on;
        } else if (cmd.index3 == 0) {
          v1state = Valve1_off;
        } else if (cmd.index3 > 1){
          v1.valve_period = cmd.index3;
          v1state = Valve1_hold;  // no change
          v1.prev_time = millis();
        }
        break;

      case 'D':
        stepper2state = S2IDLE;
        stepper1state = S1IDLE;
        v1state = Valve1_off;
        dcstate  = DC_off;
        stopMotor2();
        stopMotor1();
        calibration_off();
        valve1_off();
        break;

      case 'P':
        if (cmd.index2 > 0 && cmd.index2 <= sizeof(positions) / sizeof(positions[0])) {
          stepper1.pause_period = cmd.index3;
          stepper1.targetpos = positions[cmd.index2 - 1];
          stepper1state = MOVING_OUT;
        }
        break;

      default:
        break;
    };

    cmd.valid = false;
  }

  switch (stepper2state) {
    case MOVING_F:
      move_f();
      if (digitalRead(sensors.Sensor_f) == HIGH) {
        stepper2state = S2IDLE;
        update_motor_state();
        //updateDisplay();
      } 
      break;

    case MOVING_B:
      move_b();
      if (digitalRead(sensors.Sensor_b) == HIGH) {
        stepper2state = S2IDLE;
        update_motor_state();
        //updateDisplay();
      }  
      break;

    case S2IDLE:
      stopMotor2();
      default:
      break;
  }
  
  switch (stepper1state) {
    case MOVING_OUT:
      move_pos(stepper1.targetpos);

      if (stepper1Motor.distanceToGo() == 0) {
        digitalWrite(stepper1.enablePin, HIGH);
        stepper2state = MOVING_F;
        stepper1state = S1_S2_F;
        update_motor_state();
        setLine2(String(totalAngle, 1));
        //updateDisplay();
      }
      break;

    case S1_S2_F:
      stopMotor1();

      if (digitalRead(sensors.Sensor_f) == HIGH) {
        stepper1state = S1_Pause;
        stepper1.prev_time = millis();
        update_motor_state();
        //updateDisplay();
      }
      break;

    case S1_Pause:

      if (millis() - stepper1.prev_time >= stepper1.pause_period * 1000) {
        stepper2state = MOVING_B;
        stepper1state = S1_S2_B;
        update_motor_state();
        //updateDisplay();
      }
      break;

    case S1_S2_B:

      if (digitalRead(sensors.Sensor_b) == HIGH) {
        stepper1state = MOVING_HOME;
        update_motor_state();
        setLine2(String(totalAngle, 1));
        //updateDisplay();
      }
      break;

    case MOVING_HOME:
      move_0();

      if (digitalRead(sensors.Sensor_home) == HIGH)  {
        stepper1state = S1IDLE;
        stopMotor1();
 
        update_motor_state();
        setLine2(String(totalAngle, 1));
        //updateDisplay();

        stepper1Motor.setCurrentPosition(0); // Set home position
        AS5600_reset();
      }
      break;

    case S1IDLE:
      stopMotor1();
      default:
      break;
  }

    switch (dcstate) {
      case DC_on:
        calibration_on();
        //Serial.println("calibration_on");
        if (millis() - dcmotor.prev_time >= dcmotor.rpm_period * 1000) {
          dcstate  = DC_off;
        }
      break;

      case DC_off:
        calibration_off();
        default:
        break;
  }

    switch (v1state) {
      case Valve1_on:
        valve1_on();
        //Serial.println("calibration_on");
      break;

      case Valve1_hold:
        valve1_on();
        if (millis() - v1.prev_time >= v1.valve_period * 1000) {
          v1state = Valve1_off;
        }
      break;
   

      case Valve1_off:
        valve1_off();
        default:
        break;
  }
}



CommandIndices processSerialCommands() {
  CommandIndices cmd = {"", 0, 0, false};

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();

    if (input.startsWith("<") && input.endsWith(">")) {
      input = input.substring(1, input.length() - 1);  // Remove < >
      int firstComma = input.indexOf(',');
      int secondComma = input.indexOf(',', firstComma + 1);

      if (firstComma != -1 && secondComma != -1) {
        cmd.index1 = input.substring(0, firstComma);
        cmd.index2 = input.substring(firstComma + 1, secondComma).toInt();
        cmd.index3 = input.substring(secondComma + 1).toInt();
        cmd.valid = true;
      }
    }
  }

  return cmd;
}

void sensingFunction() {
  if (currentTime - lastSensingTime >= period_sensing) {
    lastSensingTime = currentTime;

    AS5600_increment();
  }
}

void reportFunction() {
  if (currentTime - lastReportTime >= period_report) {
    lastReportTime = currentTime;

    setLine1(stepper1StateToString(stepper1state)+ "," + stepper2StateToString(stepper2state));
    setLine2(String(totalAngle, 1));

    String e0 = String(stepper1StateToNumber(stepper1state));
    String e1 = String(stepper2StateToNumber(stepper2state));
    String e2 = String(DCStateToNumber(dcstate));
    String e3 = String(Valve1StateToNumber(v1state));
    String e4 = String(totalAngle, 0);
    String e5 = String(digitalRead(sensors.Sensor_home));
    String e6 = String(digitalRead(sensors.Sensor_f));
    String e7 = String(digitalRead(sensors.Sensor_b));
    String e8 = String(cmd_letter);

    String message = e0 + "," + e1 + "," + e2 + "," + e3 + "," + e4 + "," +
                    e5 + "," + e6 + "," + e7 + "," + e8 ;

    Serial.println(message);
    ////updateDisplay();
  }
}

