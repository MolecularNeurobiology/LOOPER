#include <AccelStepper.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_MAX31855.h>
#include <Wire.h>
#include <SPI.h>

#include "r_actuator.h"
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
int e_loop_index = 0;

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

  // Initialize heater 
  displayLine0("setup heater");
  heater_setup();
  displayLine0("heater done");
  
  // Initialize encoder
  //displayLine0("setup_encoder");
  //as5600_setup();
  //displayLine0("encoder done");

  displayLine0(" Wall_state_machine_V5, 08/29/2025" );
  Serial.println(" Wall_state_machine_V5, 08/29/2025" );
  delay(3000);
}


void loop() {
  
  currentTime = millis();
  reportFunction();
  sensingFunction();

  CommandIndices cmd = processSerialCommands();

  if (cmd.valid) {
    cmd_letter = cmd.index1.charAt(0);

    setLine0(cmd.index1 + cmd.index2 + cmd.index3);
    //Serial.println(line0Text);
    
    switch (cmd_letter) {

      case 'T':
        if (cmd.index2 == 0) {
          heaterstate  = Heater_off;
          heater.PWM = 0;

        } else if (cmd.index2 == 1) {
          heaterstate  = Heater_on;
          heater.PWM = cmd.index3;

        } else if (cmd.index2 == 2){
          heaterstate = Heater_auto;
          heaterpid.setpoint = cmd.index3;
          heaterpid.prev_time = millis();
        }
      break;

      case 'B':
        stepper2state = S2_B;
      break;

      case 'F':
        stepper2state = S2_F;
      break;

      case 'C':
        if (cmd.index2 == -1) {
          dcstate  = DC_on;
          Serial.println("Ongoing: Calibrating");

        } else if (cmd.index2 == 0) {
          dcstate  = DC_off;
          Serial.println("Ongoing: Pipette Off");

        } else if (cmd.index2 > 0){
          dcstate  = DC_hold;
          dcmotor.rpm_period = cmd.index2;
          dcmotor.prev_time = millis();
          Serial.println("Starting: Calibrating for " + String(cmd.index2) + "s");
        }
      break;

      case 'V':
        if (cmd.index3 == -1) {
          valve.v_number = cmd.index2;
          valvestate = Valve_on;
          Serial.println("Valve "+ String(cmd.index2) +" On");

        } else if (cmd.index2 == 0 && cmd.index3 == 0){
          valvestate = Valve_off_all;  // no change
          Serial.println("All Gases Off");

        } else if (cmd.index3 == 0 ) {
          valve.v_number = cmd.index2;
          valvestate = Valve_off;
          Serial.println("Valve "+ String(cmd.index2) +" Off");

        } else if (cmd.index3 > 0){
          valve.v_number = cmd.index2;
          valvestate = Valve_hold;  // no change
          valve.valve_period = cmd.index3;
          valve.prev_time = millis();
          Serial.println("Starting: Valve "+ String(cmd.index2) +" on for " + String(valve.valve_period) + "s");
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
            valve.v_number = stepper1.target_index;
            stepper1.prev_time = millis();
            Serial.println("Ongoing: On Position " + String(cmd.index2) + ", Prefilled for " + String(cmd.index3) + "s");
          }
        }
      break;

      case 'S':
        stepper1.isStandby = true;
        Serial.println("Starting: On Standby");
        
        stepper1.targetpos = positions[0];
        pstate = P_S2_B;
      break;

      case 'A':
        stepper1.isAnoxic = true;
        Serial.println("Starting: On Anoxic Air");

        if (cmd.index2 > 0 && cmd.index2 <= 4) {
          stepper1.targetpos = positions[cmd.index2 - 1];
          stepper1.pause_period = cmd.index3;
          stepper1.target_index = cmd.index2;
          valve.v_number = cmd.index2;
          Serial.println("Prefill for " + String(cmd.index3) + "s");

          pstate = P_PAUSE;  
          valvestate = Valve_on;
          stepper1.prev_time = millis();
          Serial.println("Ongoing: On Position " + String(cmd.index2) + ", Prefilled for " + String(cmd.index3) + "s");
        }
      break;

      case 'R':
        stepper1.isRoomTemp = true;
        Serial.println("Starting: On Room Air");

        stepper1.targetpos = positions[0];
        stepper1.pause_period = 0;
        pstate = P_S2_B;
        Serial.println("Ongoing: On Position 1, Gas Off");
      break;

      case 'E':
        e_loop_index = 0;
        estate = E_S2_B;
      break;

      case 'D':
        stepper2state = S2_IDLE;
        stepper1state = S1_IDLE;
        valvestate = Valve_off_all;;
        dcstate  = DC_off;
        pstate  = P_IDLE;
        estate  = E_IDLE;
        Serial.println(" The device is ready for shutdown, you may now turn off the wiring box and the main power strip.");
      break;

      case 'U':
        String startup_check = "  Starting: Startup Check";
        String instruction1 = " User input is required for startup, follow the instructions on the screen";
        String instruction2 = " If any of the test fail, let the startup sequence finish, then shut down the device by inputing <D,0,0> and call a technician";
        String instruction3 = " Align the pneumotach with the gas chamber, once it is aligned input '<E,0,0>' into the serial port";
        Serial.println(startup_check + "\n" + instruction1 + "\n" + instruction2 + "\n" + instruction3);
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
        stepper2state = S2_IDLE;
      } 
    break;

    case S2_B:
      move_b();
      if (digitalRead(sensors.Sensor_b) == HIGH) {
        stepper2state = S2_IDLE;
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
        as5600_reset();
        stepper1state = S1_IDLE;
      }
    break;

    case S1_OUT:
      move_pos(stepper1.targetpos);

      if (stepper1Motor.distanceToGo() == 0) {
        stopMotor1();
        stepper1state = S1_IDLE;
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
      //if (valvestate == Valve_on){
      //  Serial.println("valvestate is on already");
      //  break;
      // }
      valve_open(valve.v_number);
    break;

    case Valve_hold:
      valve_open(valve.v_number);
      if (millis() - valve.prev_time >= valve.valve_period * 1000) {
        valvestate = Valve_off;
        Serial.println("Finished: Valve "+ String(valve.v_number) +" on for " + String(valve.valve_period) + "s");
      }
    break;

    case Valve_off_all:
      valve_close_all();
    break;

    case Valve_off:
      // if (valvestate == Valve_off){
      //  break;
     // }
      valve_close(valve.v_number);
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
      }
    break;
    
    case P_S1_HOME:
      // S2 idle
      // S1 moves to home/pos1
      stepper1state = S1_HOME;
      stepper2state = S2_IDLE;
      move_0();

      if (digitalRead(sensors.Sensor_home) == HIGH)  {
        
        if(stepper1.isStandby){
          stepper1state = S1_IDLE;
          valvestate = Valve_off_all;;
          pstate = P_IDLE; 
          stepper1.isStandby = false;
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
          valve.v_number = stepper1.target_index;
          valvestate = Valve_on;
        } else if (stepper1.pause_period == 0 ) {
          valve.v_number = stepper1.target_index;
          valvestate = Valve_off;
        } else if (stepper1.pause_period > 0){
          //valvestate = Valve_on;
          Serial.println("Finished: On Position " + String(stepper1.target_index) + ", Prefilled for " + String(stepper1.pause_period) + "s");
        }

        if(stepper1.isAnoxic){
        stepper1.isAnoxic = false;
        Serial.println("Finished: On Anoxic Air");
        break;
        }

        if(stepper1.isRoomTemp){
        valvestate = Valve_off;
        stepper1.isRoomTemp = false;
        Serial.println("Finished: On Room Air");
        break;
        }

        pstate = P_IDLE;
      }
    break;

    case P_IDLE:
      //stepper1state = S1_IDLE;
      //stepper2state = S2_IDLE;
      default:
    break;
  }

  switch (estate) {
    case E_S2_B:
      // S2 moves away from penu
      // S1 idle
      stepper1state = S1_IDLE;
      stepper2state = S2_B; 
      
      //Serial.println("I am E_S2_B");

      if (digitalRead(sensors.Sensor_b) == HIGH) {
        estate = E_S1_HOME;
        //Serial.println("going to E_S1_HOME,"+ String(e_loop_index));
        
      }
    break;

    case E_S1_HOME:
      // S2 idle
      // S1 moves to home/pos1
      stepper1state = S1_HOME;
      stepper2state = S2_IDLE;
      move_0();

      //Serial.println("I am E_S1_HOME");

      if (digitalRead(sensors.Sensor_home) == HIGH)  {
        estate = E_S1_OUT; 
        //Serial.println("going to E_S1_OUT," + String(e_loop_index));
      }
    break;

    case E_S1_OUT:
      // S2 idle
      // S1 moves to pos
      stepper1state = S1_OUT;
      stepper2state = S2_IDLE;

      move_pos(stepper1.targetpos);
      if (stepper1Motor.distanceToGo() == 0) {
        estate = E_S2_F; 
        //Serial.println("going to E_S2_F," + String(e_loop_index));
      }

    break;

    case E_S2_F:
      // S2 moves toward penu
      // S1 idle
      stepper1state = S1_IDLE;
      stepper2state = S2_F; //S2 is moving now

     

      if (digitalRead(sensors.Sensor_f) == HIGH) {
        if (e_loop_index < 4) {
          
          if (e_loop_index == 0) {
            Serial.println("Confirming that the rotational stepper motor is properly homed:\n Going to position 2");
          }else{
            Serial.println (" Going to position " + String(e_loop_index+1));
          }
          
          stepper1.targetpos = positions[e_loop_index];
          e_loop_index++;
          estate = E_S2_B; // loop again

        } else {
          e_loop_index = 0; // reset for next round
          estate = E_V; // or next appropriate state
          //valve.v_number = 1;
          //valvestate = Valve_on;
          valve.prev_time = millis();
          Serial.println("\nIf the device locked at any point, restart the homing sequence by inputing <U,0,0>" );
          Serial.println("Testing Valves: All valves will be turned on and off in order for 5 seconds each. If you do not hear the gas flowing when a valve is turned on, wait for the startup fo finish then input <D,0,0> to shut down the device and call a technician.\n\n Valve 1" );
        }
      }

    break;

    case E_V:

      if (millis() - valve.prev_time >= 2000) {
        valve_close(valve.v_number);

        if (e_loop_index < 4) {
          e_loop_index++;
          valve.v_number = e_loop_index;
          estate = E_V; // loop again
          valvestate = Valve_on;
          valve.prev_time = millis();
          Serial.println(" Valve " + String(valve.v_number));
        } else {
          e_loop_index = 0; // reset for next round
          estate = E_C; // or next appropriate state
          valvestate = Valve_off_all;
          dcmotor.prev_time = millis();
          Serial.println("\nIf any of the valves are irresponsive, DO NOT use this device, turn it off and call a technician\n Testing Calibrating Pipette");
        }
      }

    break;

    case E_C:
      dc_on();
      if (millis() - dcmotor.prev_time >= 5000) {
          dcstate  = DC_off;
          estate = E_IDLE;
          Serial.println(" Finished: Startup Check - All Components Functional");
        }
    break;

    case E_IDLE:
      default:
    break;
  }

  switch (heaterstate) {
    case Heater_on:
      heater_on();
      digitalWrite(heater.led_pin, HIGH);
      //Serial.println("heater_on");
    break;

    case Heater_auto:
      Serial.println("Heater_auto");
      if (currentTime - heaterpid.prev_time >= heaterpid.PID_period) {
          heaterpid.prev_time  = currentTime;
          heater_auto();

          heater.ledState = !heater.ledState;
          digitalWrite(heater.led_pin, heater.ledState);
        }
    break;

    case Heater_off:
      heater_off();
      digitalWrite(heater.led_pin, LOW);
      //Serial.println("Heater_off");
      default:
    break;
  }
  
  stepper2Motor.runSpeed();
  stepper1Motor.runSpeed();
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
    
    heater_read();
    //as5600_increment();
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
    String e2 = String(dcmotorStateToNumber(dcstate));
    String e3 = String(valveStateToNumber(valvestate));
    //String e4 = String(as5600.totalAngle,0);
    String e4 = String(heater.TC_filter);
    String e5 = String(digitalRead(sensors.Sensor_home));
    String e6 = String(digitalRead(sensors.Sensor_f));
    String e7 = String(digitalRead(sensors.Sensor_b));
    String e8 = String(cmd_letter);

    String message = "["+ e0 + "," + e1 + "," + e2 + "," + e3 + "," + e4 + "," +
                    e5 + "," + e6 + "," + e7 + "," + e8 + "]";

    //Serial.println(message);
    //Serial.println(heater.TC_filter);

    //setLine0(e8);
    setLine1(e0 + "," + e1 + "," + e2 + "," + e3);
    setLine2(e5 + "," + e6 + "," + e7);
    setLine3(e4);
    updateDisplay();
   
  }
}

     