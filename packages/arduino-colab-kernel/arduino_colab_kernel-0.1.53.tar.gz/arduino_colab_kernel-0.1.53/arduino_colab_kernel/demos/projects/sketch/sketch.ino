#include <Arduino.h>

//**Global variables**

int t = 0; // Timer counter


//**Functions**

// No functions defined


//**Setup**

void setup() {
	Serial.begin(115200);
}


//**Loop**

void loop() {
	t++; // Increment timer counter
Serial.println(t); // Print timer counter to serial monitor
}

