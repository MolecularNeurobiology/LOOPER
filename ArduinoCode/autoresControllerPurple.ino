
// Current Code with endstops, no overheating motor, led indicator, and timing belt
// To add new function, Add the function letter the to Commands array and increase Comsize by the number of new functions

// [2021-0415-Tan] Re-assign the I/O pins and add VA2, VA3, VA4
// [2022-0131-Brandon] Slow down the rotational motor and adjust position 3 a few steps 
// [2022-0418-Brandon] Changed valve pins for new PCBh

// Debugging notes
///add guard safe to make sure it does not move back if it is already touching the end stop
// add abort command
// fix homing code
// add way for the machnine to detect that it is stuck and shuts off

#include <AccelStepper.h>// includes accelstepper library
//Avoid 23-53 pins on arduino mega
char prot;//character for protoype choice equal to proto but allows the proto value to remain constant throughout code
char proto;//chracter for prototype
char act = '0'; // for action
char act2 = '0';
char action;
char act3 = '0';
char act4 = '0';
char action3;


int val;// value for switch case
const int Gas1 = 32; // pin for Gas 1 [Brandon]
const int Gas2 = 38; // pin for Gas 2 [Brandon]
const int Gas3 = 44; // pin for Gas 3 [Brandon]
const int Gas4 = 50; // pin for Gas 4 [Brandon]
int pos = -1; // if you change pos, posB or pos3 here change it also at the begining of each swicht case so that the values always reset to the same numbers
int posB = 1; //a full revolution is at 400 for forward stepper and 1600 for the rotational stepper
int posho = 0;
int pos0 = 0; // endstop position
const int pos1 = -940;
const int pos2 = -530;
const int pos3 = -155;
const int pos4 = -1350;
long rothome = 975;// this should be 800 but bewcause i messed up in the placement of the flag arm of the gas housing, i needed to adjust the home for the red AGE rothome = 830 works best
const int mot = 26; // pin for DC motor [Tan]
const int led = 13; // pin for LED [Tan]
int state = LOW;
int blk = 0;
unsigned long mil; //LED Timer
unsigned long prev; //LED Timer
unsigned long inter; //LED Timer
unsigned long milt; //LED Timer
unsigned long prevt; //LED Timer
unsigned long milV;// Valve Timer
unsigned long prevV;//Valve Timer
long SecValve; //ve Timer
unsigned long milP;// Position ve Timer
unsigned long prevP;//Position ve Timer
long SecPosi; //Position ve Timer
unsigned long mmil;//calibrating motor timer
unsigned long mprev;//calibrating motor timer
long Sec; // used as timer for calibrating pipette

const int Bendstop = 11; // pin for Back End stop limit S.W. [Tan]
const int Fendstop = 10; // pin for Frond End stop limit S.W. [Tan]
const int Rotendstop = 12; // pin for Rotary End stop limit S.W. [Tan]
static boolean stopflag = false;
static boolean stopflagB = false;
static boolean rotflag = false;

// Setup for reading Serial inputs

const byte numChars = 32;
char receivedChars[numChars];
char tempChars[numChars];

char Component[numChars] = {0};
int ComponentNum = 0;
int ComponentOp = 0;

boolean newData = false;

boolean go = false; //for position code

// Set up for changin lettrer input to number
int Comsize = 12; //# of commands in my code
const int ComsizeChar = Comsize + 1;
char Commands[] = "CVPSARUBFDEZ"; //add Z for abort
int ComponentNumSwitch;
int ComponentOpSwitch ;

// debugging flags
boolean flag = true; //TBD

// starupflags
boolean startupread = false; //TBD
char Confirm;  //TBD

//delete this 
int cycle=0; 

// Stepper motors set up
AccelStepper stepper(1, 2, 3); // pin 2 is connected to PUL- on stepping driver and pin 3 is connected to DIR-. [Tan]
//Stepping driver controls the Forwards and backwards stepper motor.  (Defaults to AccelStepper::FULL4WIRE (4 pins) on 2, 3, 4, 5)
AccelStepper rotstepper(2, 5, 6); // pin 5 is connected to PUL- on stepping driver and pin 6 is connected to DIR-. [Tan]
// the positive rotational direction is the forwards direction with the angular velocity vector facing away from the pneumotach .

void setup()
{ //for physical setup just make sure to position the rotstepper at position 1 before starting the power
  stepper.setMaxSpeed(15000);
  stepper.setSpeed(15000);
  stepper.setAcceleration(15000);
  stepper.setCurrentPosition(0);
  stepper.setEnablePin(4);//ENA- pin 4 for turning motor on and off (changed from 19 to 25, to 4) [Tan]
  rotstepper.setMaxSpeed(30000);
  rotstepper.setSpeed(4000);
  rotstepper.setAcceleration(3000);
  rotstepper.setCurrentPosition(0); // sets 1 position as 0 at each startup
  rotstepper.setEnablePin(7);//ENA- pin 7 for turning motor on and off (changed from 18 to 5, to 7) [Tan]
  pinMode(Gas1, OUTPUT); //Gas 1 pin [Tan]
  pinMode(Gas2, OUTPUT); //Gas 2 pin [Tan]
  pinMode(Gas3, OUTPUT); //Gas 3 pin [Tan]
  pinMode(Gas4, OUTPUT); //Gas 4 pin [Tan]
  pinMode(led, OUTPUT);
  pinMode(mot, OUTPUT);// calibrating motor
  pinMode(Fendstop, INPUT); // reads state of endstop that is hit when the motor moves forward ( away from the nose cone)
  pinMode(Bendstop, INPUT); // reads state of endstop that is hit when the mototr moves backwards ( towards the nosecone)
  pinMode(Rotendstop, INPUT);
  prev = 0;
  inter = 1000;
  prevt = 0;
  Serial.begin(9600);
  stepper.disableOutputs();//turns off the forwards and backwards stepper at start up so motor does not over heat because it if off as a default and is only turned off to move
  rotstepper.disableOutputs();
  digitalWrite(led, HIGH);
}

//This section just includes a series of functions that move the stepper motors in specific ways

// stepperForward2 moves the linear stepper motor away from the pneumotach.
void stepperForward2() { /// add guard safe to make sure it does not move back if it is already touching the end stop// add abort command // fix homing code // add way for the machnine to detect that it is stuck and shuts off 
  if (digitalRead(Fendstop)==HIGH && digitalRead(Bendstop)==HIGH){pos=0;}//if the mocahine is not on either end of thelinear motor limit, it sets pos to 0 so that the manchine moves slowly until it hits and endstop instead of slaming into the endstop
  stepper.enableOutputs(); 
  rotstepper.enableOutputs();
  digitalWrite(led, HIGH);
 if (digitalRead(Fendstop) != LOW){
 while (digitalRead(Fendstop) != LOW) {
    stepper.moveTo(pos);
    while (stepper.currentPosition() != pos) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
      stepper.run();
    }
    pos--; // moves linear motor in increments until the endstop is pressed.
  }
 }
  if (digitalRead(Fendstop) == LOW) {
    stepper.stop();
    stepper.setCurrentPosition(0);
    stopflag = true;
    rotflag = true;
    pos = -1;
  }
  stepper.disableOutputs(); 
}
// stepperbackwards2 moves the linear stepper motor towards the pneumotach
void stepperBackwards2() {//have it set position to zero and the conditional statements are the position//try using change in button state only
if (digitalRead(Fendstop)==HIGH && digitalRead(Bendstop)==HIGH){posB=0;}
 stepper.enableOutputs(); 
  digitalWrite(led, LOW);
 if(digitalRead(Bendstop) != LOW) {//first check if the motor is at the limit before moving to ensure it does not slam into the endstop and stall 
  while (digitalRead(Bendstop) != LOW) {
    stepper.moveTo(posB);
    while (stepper.currentPosition() != posB) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
      stepper.run();
    }
    posB++; // moves the linear motor in increments until endstop is pressed
  }
 }
  if (digitalRead(Bendstop) == LOW) {
    stepper.stop();
    stepper.setCurrentPosition(0);
    stopflagB = true;
    posB = 1;
  }
  stepper.disableOutputs(); 
  rotstepper.disableOutputs();
}


// these for functions move the rotational stepper motor, note they do not control the ves
void rotstepperPosition1() {
  if (rotflag == true) {
    while (digitalRead(Rotendstop) != LOW) {
      rotstepper.moveTo(pos0);//A full revolution is 1600
      while (rotstepper.currentPosition() != pos0) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
        rotstepper.run();
      }
      pos0++;// moves the rotstepper in increments until the endstop is pressed
    }
    if (digitalRead (Rotendstop) == LOW) {
      rotstepper.setCurrentPosition(0);
      rotstepper.moveTo (pos1);
      while (rotstepper.currentPosition() != pos1) {
        rotstepper.run();
      }
      rotstepper.stop();
      rotflag = false; // try this
      stopflag = false;
      stopflagB = false;
      pos0 = 0;
    }
  }
}

void rotstepperPosition2() {
  if (rotflag == true) {
    while (digitalRead(Rotendstop) != LOW) {
      rotstepper.moveTo(pos0);//A full revolution is 1600
      while (rotstepper.currentPosition() != pos0) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
        rotstepper.run();
      }
      pos0++;// moves the rotstepper in increments until the endstop is pressed
    }
    if (digitalRead (Rotendstop) == LOW) {
      rotstepper.setCurrentPosition(0);
      rotstepper.moveTo (pos2);
      while (rotstepper.currentPosition() != pos2) {
        rotstepper.run();
      }
      rotstepper.stop();
      rotflag = false; // try this
      stopflag = false;
      stopflagB = false;
      pos0 = 0;
    }
  } 
}

void rotstepperPosition3()
{ 
  if (rotflag == true) {
    while (digitalRead(Rotendstop) != LOW) {
      rotstepper.moveTo(pos0);
      while (rotstepper.currentPosition() != pos0) {
        rotstepper.run();
      }
      pos0++;// moves the rotstepper in increments until the endstop is pressed
    }
    if (digitalRead (Rotendstop) == LOW) {
      rotstepper.setCurrentPosition(0);
      rotstepper.moveTo(pos3);
      while (rotstepper.currentPosition() != pos3) {
        rotstepper.run();
      }
      rotstepper.stop();
      rotflag = false; // try this
      stopflag = false;
      stopflagB = false;
      pos0 = 0;
    }
  } 
}

void rotstepperPosition4()
{ 
  if (rotflag == true) {
    while (digitalRead(Rotendstop) != LOW) {
      rotstepper.moveTo(pos0);//A full revolution is 1600
      while (rotstepper.currentPosition() != pos0) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
        rotstepper.run();
      }
      pos0++;// moves the rotstepper in increments until the endstop is pressed
    }
    if (digitalRead(Rotendstop) == LOW) {
      rotstepper.setCurrentPosition(0);
      rotstepper.moveTo (pos4);
      while (rotstepper.currentPosition() != pos4) {
        rotstepper.run();
      }
      rotstepper.stop();
      rotflag = false; // try this, make them into booleans
      stopflag = false;
      stopflagB = false;
      pos0 = 0;
    }

  } 

}

// This function is for blinking the LED
void blinking() {
  mil = millis();
  milt = millis();
  prevt = milt;
  if (mil - prev >= inter) { // inter is set in the void setup
    if (state == LOW) {
      state = HIGH;
    }
    else {
      state = LOW;
    }
    digitalWrite(led, state);
    while (millis() - prevt <= 1000) {};
    prev = mil;
  }
}

// This section conatisn the list of functions that can be called through the serial port

void Calibrate(long Cals) {
  long CalsInt = Cals;
  if (CalsInt == -1) {
    Serial.println("Ongoing: Calibrating");
    digitalWrite(mot, HIGH);
  }
  if (CalsInt == 0) {
    Serial.println("Ongoing: Pipette Off");
    digitalWrite(mot, LOW);
  }
  if (CalsInt != 0 && CalsInt != -1) {
    Sec = 1000 * CalsInt;
    String action_label = "Starting: Calibrating for ";
    String calibration_time = String(Cals);
    String time_unit = "s";
    Serial.println(action_label + calibration_time + time_unit);
    digitalWrite(mot, HIGH);
    mmil = millis();
    mprev = mmil;
    while (millis() - mprev <= Sec) {};// wait for given seconds
    digitalWrite(mot, LOW);
    Serial.println("Finished: Calibrating");
  }
}

void Valve(int ValveInt, long OpInt) { // Inputs are intergers
  // Note putting in a number greater than 4 for Valve could cause the program to crash since
  String current_label = "Valve ";
  String identify_valve = String(ValveInt);
  String total_time = String(OpInt);
  String time_unit = "s";
  //matrices are used here so a number greater then 4 will not be accepted aka nothing will happen
  SecValve = 1000 * OpInt;
  int valves[] = {Gas1, Gas2, Gas3, Gas4}; // sets up matrix with Gas pins, note the values are intergers
  //Turn off valve
  if (OpInt == 0 && ValveInt < 5 && ValveInt > 0) {
    digitalWrite(valves[ValveInt - 1], LOW); // for ie. if Op=1, this lines turns off the pin number in
    //position 0 of the valves matrix which is Gas1 (Gas1 is an interger and stores the pin numbers)
    String valve_off = " Off";
    Serial.println(current_label + identify_valve + valve_off);
  }
  //Turn on valve
  if (OpInt == -1 && ValveInt < 5 && ValveInt > 0) {
    digitalWrite(valves[ValveInt - 1], HIGH);
    String valve_on = " On";
    Serial.println(current_label + identify_valve + valve_on);
  }
  //Turn off all valves
  if (ValveInt == 0 && OpInt == 0) {
    digitalWrite (Gas1, LOW);
    digitalWrite (Gas2, LOW);
    digitalWrite (Gas3, LOW);
    digitalWrite (Gas4, LOW);
    Serial.println("All Gases Off");
  }
  //Turn on valve for specified time
  else {
    if (ValveInt < 5 && ValveInt > 0 && OpInt != -1 && OpInt != 0) {
      String valve_start = "Starting: Valve ";
      String specify_time = " on for ";
      Serial.println(valve_start + identify_valve + specify_time + total_time + time_unit);
      digitalWrite(valves[ValveInt - 1], HIGH);
      milV = millis();
      prevV = milV;
      while (millis() - prevV <= SecValve) {};
      digitalWrite(valves[ValveInt - 1], LOW);
      String valve_finish = "Finished: Valve ";
      Serial.println(valve_finish + identify_valve + specify_time + total_time + time_unit);
    }
  }
}

void Pos(int PosiInt, long GasInt) { // Inputs are intergers
  String prefill_label = "Prefill for ";
  String prefill_time = String(GasInt);
  String time_unit = "s";
  String position_label = "Ongoing: On Position ";
  String identify_position = String(PosiInt);
  Serial.println(prefill_label + prefill_time + time_unit);
  int valves[] = {Gas1, Gas2, Gas3, Gas4};
  SecPosi = 1000 * GasInt;
  //Go to posi and do not turn on the valve
  if (GasInt == 0 && PosiInt < 5 && PosiInt > 0) {
    String gas_off = ", Gas Off";
    Serial.println(position_label + identify_position + gas_off);
    digitalWrite(valves[PosiInt - 1], LOW); // turn off valve
    if (PosiInt == 1) {
      stepperForward2(); rotstepperPosition1(); stepperBackwards2();
    }
    if (PosiInt == 2) {
      stepperForward2(); rotstepperPosition2(); stepperBackwards2();
    }
    if (PosiInt == 3) {
      stepperForward2(); rotstepperPosition3(); stepperBackwards2();
    }
    if (PosiInt == 4) {
      stepperForward2(); rotstepperPosition4(); stepperBackwards2();
    }
  }
  // Go to Position and Turn on the Valve
  if (GasInt == -1 && PosiInt < 5 && PosiInt > 0) {
    digitalWrite(valves[PosiInt - 1], HIGH); // turn on valve
    String gas_on = ", Gas On";
    Serial.println(position_label + identify_position + gas_on);
    if (PosiInt == 1) {
      stepperForward2(); rotstepperPosition1(); stepperBackwards2();
    }
    if (PosiInt == 2) {
      stepperForward2(); rotstepperPosition2(); stepperBackwards2();
    }
    if (PosiInt == 3) {
      stepperForward2(); rotstepperPosition3(); stepperBackwards2();
    }
    if (PosiInt == 4) {
      stepperForward2(); rotstepperPosition4(); stepperBackwards2();
    }
  }
  // Turn on gas for specified time first, then go to position and keep gas on
  else {
    if (PosiInt < 5 && PosiInt > 0 && GasInt != 0 && GasInt != -1) {
      String prefill_length = ", Prefilled for ";
      Serial.println(position_label + identify_position + prefill_length + prefill_time + time_unit);
      digitalWrite(valves[PosiInt - 1], HIGH);
      milP = millis();
      prevP = milP;
      while (millis() - prevP <= SecPosi) {
        go = false;
      }
      if ( millis() - prevP >= SecPosi) {
        go = true;
      }

      if (PosiInt == 1 && go == true) {
        stepperForward2(); rotstepperPosition1(); stepperBackwards2();
        go = false;
      }
      if (PosiInt == 2 && go == true) {
        stepperForward2(); rotstepperPosition2(); stepperBackwards2();
        go = false;
      }
      if (PosiInt == 3 && go == true) {
        stepperForward2(); rotstepperPosition3(); stepperBackwards2();
        go = false;
      }
      if (PosiInt == 4 && go == true) {
        stepperForward2(); rotstepperPosition4(); stepperBackwards2();
        go = false;
      }
      
      String position_finish = "Finished: On Position ";
      Serial.println(position_finish + identify_position + prefill_length + prefill_time + time_unit);
    }
  }
}

void Standby() {
  Serial.println("Starting: On Standby");
  stepperForward2(); rotstepperPosition1();
  Valve(0, 0);
  Serial.println("Finished: On Standby");
}

void Anoxic(int AnoxPos, int T) {
  Serial.println("Starting: On Anoxic Air");
  Pos(AnoxPos, T);
  Serial.println("Finished: On Anoxic Air");
}

void Room() {
  Serial.println("Starting: On Room Air");
  Pos(1, 0);
  digitalWrite(Gas3, LOW); 
  digitalWrite(Gas2, LOW); 
  digitalWrite(Gas4, LOW); 
  Serial.println("Finished: On Room Air");
}

void Startup() {
  String startup_check = "  Starting: Startup Check";
  String instruction1 = " User input is required for startup, follow the instructions on the screen";
  String instruction2 = " If any of the test fail, let the startup sequence finish, then shut down the device by inputing <D,0,0> and call a technician";
  String instruction3 = " Align the pneumotach with the gas chamber, once it is aligned input '<E,0,0>' into the serial port";
  Serial.println(startup_check + "\n" + instruction1 + "\n" + instruction2 + "\n" + instruction3);
}

void StartupPartB() {
  // if the pneumotach is too far left of the hole, increase the value of rothome,
  // if its too far right, decrease the value of rothome
  // user aligns the pneumotach and syringe to set the zero position
  stepperForward2(); // move away from pneumotach
  if (rotflag == true) { // move to position three to set endstop position to zero
    rotstepper.enableOutputs();
    while (digitalRead(Rotendstop) != LOW) {
      rotstepper.moveTo(posho);//A full revolution is 1600
      while (rotstepper.currentPosition() != posho) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
        rotstepper.run();
      }
      posho++;// moves the rotstepper in increments until the endstop is pressed
    }
    if (digitalRead(Rotendstop) == LOW) {
      rotstepper.setCurrentPosition(0); // set
      rotstepper.moveTo(pos1);
      while (rotstepper.currentPosition() != pos1) {
        rotstepper.run();
      }
      rotstepper.stop();
      rotstepper.disableOutputs();
      rotflag = false; // try this, make them into booleans
      stopflag = false;
      stopflagB = false;
    }
  }
  stepperBackwards2();
  // rotate to all four positions and set the positions
  Serial.println("Confirming that the rotational stepper motor is properly homed:\n Going to position 2");
  stepperForward2(); rotstepperPosition2(); stepperBackwards2();
  Serial.println (" Going to position 3");
  stepperForward2(); rotstepperPosition3(); stepperBackwards2();
  Serial.println (" Going to position 4");
  stepperForward2(); rotstepperPosition4(); stepperBackwards2();
  Serial.println (" Going to position 1");
  stepperForward2(); rotstepperPosition1(); stepperBackwards2();
  Serial.println("\nIf the device locked at any point, restart the homing sequence by inputing <U,0,0>" );
  // Turn on and off all gas valves
  Serial.println("Testing Valves: All valves will be turned on and off in order for 5 seconds each. If you do not hear the gas flowing when a valve is turned on, wait for the startup fo finish then input <D,0,0> to shut down the device and call a technician.\n\n Valve 1");
  Valve(1, 5);
  Valve(1, 0);
  Serial.println (" Valve 2");
  Valve(2, 5);
  Valve(2, 0);
  Serial.println (" Valve 3");
  Valve(3, 5);
  Valve(3, 0);
  Serial.println (" Valve 4");
  Valve(4, 5);
  Valve(4, 0);
  Serial.println("\nIf any of the valves are irresponsive, DO NOT use this device, turn it off and call a technician\n Testing Calibrating Pipette");
  Calibrate (30);
  Serial.println(" Finished: Startup Check - All Components Functional");
  startupread = false;
}
void ShutDown () {//add command to shut off all valves and other electrical components
  stepperForward2(); rotstepperPosition1(); stepperBackwards2();
  stepper.disableOutputs();
  rotstepper.disableOutputs();
  digitalWrite(mot, LOW);
  Serial.println(" The device is ready for shutdown, you may now turn off the wiring box and the main power strip.");
}

void ABORT() {
  // disable current to stepper motors
  stepper.disableOutputs();
  rotstepper.disableOutputs();
  // close current in transistor for calibating motor (turn motor off)
  digitalWrite(mot, LOW);
  //turn off the led
  digitalWrite(led, LOW);
  //turn off all valves
  digitalWrite (Gas1, LOW);
  digitalWrite (Gas2, LOW);
  digitalWrite (Gas3, LOW);
  digitalWrite (Gas4, LOW);
  Serial.println("ABORTED");
}


// This section contains all the functions for reading the serial port to call the functions above
//note all inputs must be preceeded by '<' and ended by '>', see input guide.
// Function to read data send from the serial port and store it in receivedChars
void recvdata () {
  static boolean recvInProgress = false; // the static part allows this boolean to keep its value between functions
  static byte ndx = 0;
  char startMarker = '<';
  char endMarker = '>';
  char recv;

  while (Serial.available() > 0 && newData == false) {
    recv = Serial.read();
    if (recvInProgress == true) {
      if (recv != endMarker) {
        receivedChars[ndx] = recv;
        ndx++;
        if (ndx >= numChars) {
          ndx = numChars - 1;
        }
      }
      else {
        receivedChars[ndx] = '\0';
        recvInProgress = false;
        ndx = 0;
        newData = true;
      }
    }
    else if ( recv == startMarker) {
      recvInProgress = true;
    }
  }
}


void parseData() { // split the data into its parts
  char *  strtokIndx; // this is used by strtok() as an index

  strtokIndx = strtok(tempChars, ",");  // get the first part - the string
  strcpy(Component, strtokIndx); // copy it to messageFromPC

  strtokIndx = strtok(NULL, ","); // this continues where the previous call left off
  ComponentNum = atoi(strtokIndx);  // convert this part to an integer

  strtokIndx = strtok( NULL, ",");
  ComponentOp = atoi(strtokIndx);
}

void showParsedData() {

  String component_label = "Component ";
  String identify_component = String(Component);
  String number_label = "Number ";
  String comp_num = String(ComponentNum);
  String op_label = "Operation ";
  String comp_op = String(ComponentOp);
  Serial.println(component_label + identify_component + "\n" + number_label + comp_num + "\n" + op_label + comp_op);

}

void loop() {
  // Serial.print("Start Loop"); Tan testing program
   recvdata();
  // If their is new data take it out, parse the data, and set them to input terms for the switch case
  if (newData == true) {
    strcpy(tempChars, receivedChars);
    parseData();
    // showParsedData (); // short term to check data was pared properly
    newData = false;
    String(ComponentSwitch) = Component;
    int ComponentNumSwitch = ComponentNum;
    int ComponentOpSwitch = ComponentOp;
    // turning Componentswitch into a number
    for (int i = 0; i < Comsize; i++) {
      char temp = Commands[i];
      char tempComp[2];
      ComponentSwitch.toCharArray(tempComp, 2);
      //  Serial.println (temp);Serial.println(tempComp);//TBD
      if (Commands[i] == tempComp[0]) {
        int val = i;
        //Serial.print(val); //TBD
        switch (val) {
          case 0: // Calibrate
            Calibrate(ComponentNumSwitch);
            break;
          case 1: // Valves
            Valve(ComponentNumSwitch, ComponentOpSwitch);
            break;
          case 2: // Position
            Pos(ComponentNumSwitch, ComponentOpSwitch);
            break;
          case 3: //Standby
            Standby();
            break;
          case 4: // Anoxic
            Anoxic(ComponentNumSwitch, ComponentOpSwitch);
            break;
          case 5: // Room
            Room();
            break;
          case 6: // Startup
            Startup();
            break;
          case 7: // move towards mouse
            stepperBackwards2();
            break;
          case 8: // move away from mouse
            stepperForward2();
            break;
          case 9: // Shutdown
            ShutDown();
            break;
          case 10: // StartupPartB
            StartupPartB();
            break;
          case 11: 
            ABORT();
            break;
          
        }
        break;
      }
    }
  }

//add ABOrt code to this portion of the code 

 
}
