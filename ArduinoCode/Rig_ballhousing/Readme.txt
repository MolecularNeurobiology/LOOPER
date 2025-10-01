The rig_ballhounding_main modify function
	stepperForward2
	stepperBackwards2
	rotstepperPosition1
	rotstepperPosition2
	rotstepperPosition3
	rotstepperPosition4
to fix the ballhousing issue caused by sensor bouncing. 
Other than these functions, it will be exactly same as the autoresControllerPurple


The rig_ballhounding_test function is a testing program that will continuously run the motor to each position over & over again. It doesn't need Pi.  
9/4/2025

rig_ballhounding_switch_test
Just digitally read three switches and plot their response. This program is used to test if the switches are functional


Test & flash procedure
1. Unplug the USB port from the Arduino.
2. Flash rig_ballhounding_switch_test to the Arduino. 
3. Open the Tool-serial monitor, manually touch each switch, and see if the plot changes. Adjust switch position or replace if necessary.
4. Flash rig_ballhounding_test to the Arduino. 
5. Run the test for 1 hour, and see if any jamming happens/
6. Flash rig_ballhounding_main, put the USBcable back to Arduino

9/5/2025
