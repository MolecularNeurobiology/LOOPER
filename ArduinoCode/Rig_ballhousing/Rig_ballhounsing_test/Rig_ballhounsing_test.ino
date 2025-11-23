#include <AccelStepper.h>

AccelStepper stepper(1, 2, 3); // pin 2 is connected to PUL- on stepping driver and pin 3 is connected to DIR-. [Tan]
AccelStepper rotstepper(2, 5, 6); // pin 5 

const int Bendstop = 11; // pin for Back End stop limit S.W. [Tan]
const int Fendstop = 10; // pin for Frond End stop limit S.W. [Tan]
const int Rotendstop = 12; // pin for Rotary End stop limit S.W. [Tan]
static boolean stopflag = false;
static boolean stopflagB = false;
static boolean rotflag = false;

int pos = -1; // if you change pos, posB or pos3 here change it also at the begining of each swicht case so that the values always reset to the same numbers
int posB = 1; //a full revolution is at 400 for forward stepper and 1600 for the rotational stepper
int posho = 0;
int pos0 = 0; // endstop position
const int pos1 = -940;
const int pos2 = -530;
const int pos3 = -155;
const int pos4 = -1350;
long rothome = 975;// this should be 800 but bewcause i messed up in the placement of the flag arm of the gas housing, i needed to adjust the home for the red AGE rothome = 830 works best


void setup() {
  stepper.setMaxSpeed(15000);
  stepper.setSpeed(15000);
  stepper.setAcceleration(15000);
  stepper.setCurrentPosition(0);
  stepper.setEnablePin(4);//ENA- pin 4 for turning motor on and off (changed from 19 to 25, to 4) [Tan]
  rotstepper.setMaxSpeed(30000);
  rotstepper.setSpeed(4000);
  rotstepper.setAcceleration(3000);
  rotstepper.setCurrentPosition(0); // sets 1 position as 0 at each startup
  rotstepper.setEnablePin(7);//ENA- pin

  // Initialize sensor pins
  pinMode(Fendstop, INPUT); // reads state of endstop that is hit when the motor moves forward ( away from the nose cone)
  pinMode(Bendstop, INPUT); // reads state of endstop that is hit when the mototr moves backwards ( towards the nosecone)
  pinMode(Rotendstop, INPUT);

  Serial.begin(9600); // For debugging
  stepper.disableOutputs();//turns off the forwards and backwards stepper at start up so motor does not over heat because it if off as a default and is only turned off to move
  rotstepper.disableOutputs();
}

void loop() {
  // Move to position 1
  stepperForward2();
  delay(1000);

  rotstepperPosition1();
  delay(1000);

  stepperBackwards2();
  delay(1000);

  // Move to position 2
  stepperForward2();
  delay(1000);

  rotstepperPosition2();
  delay(1000);

  stepperBackwards2();
  delay(1000);

  // Move to position 3
  stepperForward2();
  delay(1000);

  rotstepperPosition3();
  delay(1000);

  stepperBackwards2();
  delay(1000);

  // Move to position 4
  stepperForward2();
  delay(1000);

  rotstepperPosition4();
  delay(1000);

  stepperBackwards2();
  delay(1000);
}

void stepperForward2() { /// add guard safe to make sure it does not move back if it is already touching the end stop// add abort command // fix homing code // add way for the machnine to detect that it is stuck and shuts off 
  if (digitalRead(Fendstop)==HIGH && digitalRead(Bendstop)==HIGH){
    pos=0;
  }//if the mocahine is not on either end of thelinear motor limit, it sets pos to 0 so that the manchine moves slowly until it hits and endstop instead of slaming into the endstop
  stepper.enableOutputs(); 
  rotstepper.enableOutputs();  

  while (digitalRead(Fendstop) != LOW) {
    stepper.moveTo(pos);
    while (stepper.currentPosition() != pos) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
      stepper.run();
    }
    pos--; // moves linear motor in increments until the endstop is pressed.
  }

  // --- Debounced confirm Require 4 of 5 reads (spaced by 2 ms) to be PRESSED before zeroing.
  int hits = 0;
  for (int i = 0; i < 5; ++i) {
    if (digitalRead(Fendstop) == LOW) hits++;
    delay(2);
  }

  if (hits >= 4) {
    stepper.stop();
    stepper.setCurrentPosition(0);
    stopflag = true;
    rotflag = true;
    pos = -1;
  }

  stepper.disableOutputs(); 
}
// Function to move stepper1 clockwise until Sensor_back is high
void stepperBackwards2() {//have it set position to zero and the conditional statements are the position//try using change in button state only
  if (digitalRead(Fendstop)==HIGH && digitalRead(Bendstop)==HIGH){
  posB=0;
  }

  stepper.enableOutputs(); 
  
  if(digitalRead(Bendstop) != LOW) {//first check if the motor is at the limit before moving to ensure it does not slam into the endstop and stall 
    while (digitalRead(Bendstop) != LOW) {
      stepper.moveTo(posB);
      while (stepper.currentPosition() != posB) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
        stepper.run();
      }
      posB++; // moves the linear motor in increments until endstop is pressed
    }
  }

  // --- Debounced confirm Require 4 of 5 reads (spaced by 2 ms) to be PRESSED before zeroing.
  int hits = 0;
  for (int i = 0; i < 5; ++i) {
    if (digitalRead(Bendstop) == LOW) hits++;
    delay(2);
  }

  if (hits >= 4) {
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
    
     // --- Debounced confirm Require 4 of 5 reads (spaced by 2 ms) to be PRESSED before zeroing.
    int hits = 0;
    for (int i = 0; i < 3; ++i) {
      if (digitalRead(Rotendstop) == LOW) hits++;
      delay(2);
    }

    if (hits >= 2) {
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

    // --- Debounced confirm Require 4 of 5 reads (spaced by 2 ms) to be PRESSED before zeroing.
    int hits = 0;
    for (int i = 0; i < 3; ++i) {
      if (digitalRead(Rotendstop) == LOW) hits++;
      delay(2);
    }

    if (hits >= 2) {
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

void rotstepperPosition3(){ 
  if (rotflag == true) {
    while (digitalRead(Rotendstop) != LOW) {
      rotstepper.moveTo(pos0);
      while (rotstepper.currentPosition() != pos0) {
        rotstepper.run();
      }
      pos0++;// moves the rotstepper in increments until the endstop is pressed
    }

    int hits = 0;
    for (int i = 0; i < 3; ++i) {
      if (digitalRead(Rotendstop) == LOW) hits++;
      delay(2);
    }
    
    if (hits >= 2) {
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

void rotstepperPosition4(){ 
  if (rotflag == true) {
    while (digitalRead(Rotendstop) != LOW) {
      rotstepper.moveTo(pos0);//A full revolution is 1600
      while (rotstepper.currentPosition() != pos0) { // The while statements are important!! If they are removed the steppers will not go to the proper positions
        rotstepper.run();
      }
      pos0++;// moves the rotstepper in increments until the endstop is pressed
    }

    int hits = 0;
    for (int i = 0; i < 3; ++i) {
      if (digitalRead(Rotendstop) == LOW) hits++;
      delay(2);
    }

    if (hits >= 2) {
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