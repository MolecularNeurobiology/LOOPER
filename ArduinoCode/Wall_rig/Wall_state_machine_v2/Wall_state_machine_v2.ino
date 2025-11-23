#include <AccelStepper.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>

#include "r_stepper.h"
#include "r_display.h"
#include "r_pcc.h"

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
  dc_setup();
  displayLine0("DC done");

  // Initialize encoder
  displayLine0("setup_encoder");
  AS5600_setup();
  displayLine0("encoder done");
}


void loop() {
  
  currentTime = millis();
 // reportFunction();
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
        stepper2state  = S2_B;
        break;

      case 'F':
        stepper2state  = S2_F;
        break;

      case 'C':
        if (cmd.index3 == -1) {
          dcstate  = DC_on;
          Serial.println("Ongoing: Calibrating");

        } else if (cmd.index3 == 0) {
          dcstate  = DC_off;
          Serial.println("Ongoing: Pipette Off");

        } else if (cmd.index3 != 0 && cmd.index3 != -1){
          dcstate  = DC_hold;
          dcmotor.rpm_period = cmd.index2;
          dcmotor.prev_time = millis();
          Serial.println("Starting: Calibrating for " + String(cmd.index2) + "s");
        }
        break;

      case 'V':
        if (cmd.index3 == -1) {
          valvestate = Valve_on;
          Serial.println("Valve 1 On");

        } else if (cmd.index3 == 0 || cmd.index2 == 0) {
          valvestate = Valve_off;
          Serial.println("Valve 1 Off");

        } else if (cmd.index3 > 0){
          valvestate = Valve_hold;  // no change
          valve.valve_period = cmd.index3;
          valve.prev_time = millis();
          Serial.println("Starting: Valve 1 on for " + String(valve.valve_period) + "s");

        }
      break;

      case 'P':
        if (cmd.index2 > 0 && cmd.index2 <= 4) {
          stepper1.targetpos = positions[cmd.index2 - 1];
          stepper1.pause_period = cmd.index3;
          stepper1.target_index = cmd.index2;
          Serial.println("Prefill for " + String(cmd.index3) + "s");

          if (cmd.index3 == -1) {
            pstate = P_S2_B;
            Serial.println("Ongoing: On Position " + String(cmd.index2) + ", Gas On");

          } else if (cmd.index3 == 0 ) {
            pstate = P_S2_B;
            Serial.println("Ongoing: On Position " + String(cmd.index2) + ", Gas Off");

          } else if (cmd.index3 > 0){
            pstate = P_PAUSE;  // no change
            valvestate = Valve_on;
            stepper1.prev_time = millis();
            Serial.println("Ongoing: On Position " + String(cmd.index2) + ", Prefilled for " + String(cmd.index3) + "s");
          }
        }
      break;

      case 'S':
        pstate = P_S2_B;
        stepper1.standby = true;
        Serial.println("Starting: On Standby");
      break;

      case 'A':
        stepper1.anoxic = true;
        Serial.println("Starting: On Anoxic Air");

        if (cmd.index2 > 0 && cmd.index2 <= 4) {
          stepper1.targetpos = positions[cmd.index2 - 1];
          stepper1.pause_period = cmd.index3;
          stepper1.target_index = cmd.index2;
          Serial.println("Prefill for " + String(cmd.index3) + "s");

          //stepper1state = S1_Pause;  // no change
          valvestate = Valve_on;
          stepper1.prev_time = millis();
          Serial.println("Ongoing: On Position " + String(cmd.index2) + ", Prefilled for " + String(cmd.index3) + "s");
        }
      break;

      case 'R':
        stepper1.room = true;
        Serial.println("Starting: On Room Air");

        stepper1.targetpos = positions[0];
        stepper1.pause_period = 0;
        pstate = P_S2_B;
        Serial.println("Ongoing: On Position 1, Gas Off");
      break;

      case 'U':
        String startup_check = "  Starting: Startup Check";
        String instruction1 = " User input is required for startup, follow the instructions on the screen";
        String instruction2 = " If any of the test fail, let the startup sequence finish, then shut down the device by inputing <D,0,0> and call a technician";
        String instruction3 = " Align the pneumotach with the gas chamber, once it is aligned input '<E,0,0>' into the serial port";
        Serial.println(startup_check + "\n" + instruction1 + "\n" + instruction2 + "\n" + instruction3);
      break;

      case 'E':
        Serial.println(startup_check + "\n" + instruction1 + "\n" + instruction2 + "\n" + instruction3);
      break;

      case 'D':
        stepper2state = S2_IDLE;
        stepper1state = S1_IDLE;
        valvestate = Valve_off;
        dcstate  = DC_off;
        Serial.println(" The device is ready for shutdown, you may now turn off the wiring box and the main power strip.");
      break;

      default:
      break;
    };

    cmd.valid = false;
  }

  switch (stepper2state) {
    case S2_F:
      move_f();
      if (digitalRead(sensors.Sensor_f) == HIGH) {
        stopMotor2();
        stepper2state = S2_IDLE;
        //updateDisplay();
      } 
    break;

    case S2_B:
      move_b();
      if (digitalRead(sensors.Sensor_b) == HIGH) {
        stopMotor2();
        stepper2state = S2_IDLE;
        //updateDisplay();
      }  
    break;

    case S2_IDLE:
      stopMotor2();
      default:
    break;
  }
  
  switch (stepper1state) {
    case S1_HOME:
      move_0();

      if (digitalRead(sensors.Sensor_home) == HIGH)  {
        stopMotor1();
        stepper1Motor.setCurrentPosition(0); // Set home position
        AS5600_reset();
        stepper1state = S1_IDLE;
      }
    break;

    case S1_OUT:
      move_pos(stepper1.targetpos);

      if (stepper1Motor.distanceToGo() == 0) {
        stopMotor1();
        stepper1state = S1_IDLE;
        //updateDisplay();
      }
    break;

    case S1_IDLE:
      stopMotor1();
      default:
    break;
  }

  switch (dcstate) {
    case DC_on:
      dc_on();
    break;

    case DC_hold:
      dc_on();
      if (millis() - dcmotor.prev_time >= dcmotor.rpm_period * 1000) {
          dcstate  = DC_off;
          Serial.println("Finished: Calibrating");
        }
    break;

    case DC_off:
      dc_off();
      default:
    break;
  }

  switch (valvestate) {
    case Valve_on:
      if (valvestate == Valve_on){
        break;
      }
      
      valve_on(1);
    break;

    case Valve_hold:
      valve_on(1);
      if (millis() - valve.prev_time >= valve.valve_period * 1000) {
        valvestate = Valve_off;
        Serial.println("Finished: Valve 1 on for " + String(valve.valve_period) + "s");
      }
    break;

    case Valve_off:
      if (valvestate == Valve_off){
        break;
      }
      valve_off(1);
      default:
    break;
    
  }

  switch (pstate) {
    case P_PAUSE:
      // for pre-fill, turn on valve, no motor movement
      stepper1state = S1_IDLE;
      stepper2state = S2_IDLE;
      if (millis() - stepper1.prev_time >= stepper1.pause_period * 1000) {
        pstate = P_S2_B;  
      }
    break;

    case P_S2_B:
      // S2 moves away from penu
      // S1 idle
      stepper1state = S1_IDLE;
      stepper2state = S2_B; 
      
      if (digitalRead(sensors.Sensor_b) == HIGH) {
        pstate = P_S1_HOME;
        //setLine2(String(totalAngle, 1));
        //updateDisplay();
      }
    break;
    
    case P_S1_HOME:
      // S2 idle
      // S1 moves to home/pos1
      stepper1state = S1_HOME;
      stepper2state = S2_IDLE;
      move_0();

      if (digitalRead(sensors.Sensor_home) == HIGH)  {
        
        if(stepper1.standby){
          stepper1state = S1_IDLE;
          valvestate = Valve_off;
          stepper1.standby = false;
          Serial.println("Finished: On Standby");
          break;
        }
        pstate = P_S1_OUT; 
      }
    break;

    case P_S1_OUT:
      // S2 idle
      // S1 moves to pos
      stepper1state = S1_OUT;
      stepper2state = S2_IDLE;
      move_pos(stepper1.targetpos);

      if (stepper1Motor.distanceToGo() == 0) {
        pstate = P_S2_F; 
      }
    break;

    case P_S2_F:
      // S2 moves toward penu
      // S1 idle
      stepper1state = S1_IDLE;
      stepper2state = S2_F; //S2 is moving now

      if (digitalRead(sensors.Sensor_f) == HIGH) {
        
        if (stepper1.pause_period == -1) {
          valvestate = Valve_on;
        } else if (stepper1.pause_period == 0 ) {
          valvestate = Valve_off;
        } else if (stepper1.pause_period > 0){
          valvestate = Valve_on;
          Serial.println("Finished: On Position " + String(stepper1.target_index) + ", Prefilled for " + String(stepper1.pause_period) + "s");
        }

        if(stepper1.anoxic){
        stepper1.anoxic = false;
        Serial.println("Finished: On Anoxic Air");
        break;
        }

        if(stepper1.room){
        valvestate = Valve_off;
        stepper1.room = false;
        Serial.println("Finished: On Room Air");
        break;
        }

        pstate = P_IDLE;
      }
    break;

    case P_IDLE:
      stepper1state = S1_IDLE;
      stepper2state = S2_IDLE;
      default:
    break;
  }

  /*
  switch (estate) {
    case E_S2_B:
      stepper2state = MOVING_B;
      if (stepper2state == S2_IDLE) {
        estate = E_S1_1;
      } 
    break;

    case E_S1_1:
      move_b();
      stepper1state = MOVING_HOME;
      if (stepper2state == S2_IDLE) {
        
      }  
    break;

    case E_IDLE:
      default:
    break;
  }
  */

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

    //AS5600_increment();
  }
}

void reportFunction() {
  if (currentTime - lastReportTime >= period_report) {
    lastReportTime = currentTime;
    /*
    setLine1(stepper1StateToString(stepper1state)+ "," + stepper2StateToString(stepper2state));
    setLine2(String(totalAngle, 1));
    */
    String e0 = String(stepper1StateToNumber(stepper1state));
    String e1 = String(stepper2StateToNumber(stepper2state));
    String e2 = String(DCStateToNumber(dcstate));
    String e3 = String(ValveStateToNumber(valvestate));
    String e4 = String(totalAngle, 0);
    String e5 = String(digitalRead(sensors.Sensor_home));
    String e6 = String(digitalRead(sensors.Sensor_f));
    String e7 = String(digitalRead(sensors.Sensor_b));
    String e8 = String(cmd_letter);

    String message = "["+ e0 + "," + e1 + "," + e2 + "," + e3 + "," + e4 + "," +
                    e5 + "," + e6 + "," + e7 + "," + e8 + "]";

    Serial.println(message);
    ////updateDisplay();
   
  }
}

