/* NFC Door Lock - Thunderbird12 Code
 * Author: Stefen Sharkey
 * Date: December 6, 2017
 * School: Monroe Community College
 * Course: Computer Science 202 - Embedded Programming in C and Assembly
 * Professor: George Fazekas
 */

#include <hidef.h>      /* common defines and macros */
#include <mc9s12dg256.h>     /* derivative information */
#include "main_asm.h" /* interface to the assembly module */
#include "queue.h"
#pragma LINK_INFO DERIVATIVE "mc9s12dg256b"

// Serial0 baud rate
#define SERIAL0_BAUD_RATE   9600

// Define the pin the relay is connected to.
#define RELAY_PIN           0x10

char c = 0;
int x;
int pitch;
unsigned int ticks = 0;

int unlocking = 0;

void power_mode(void);
void auth_success(void);
void auth_failed(void);

void lock(void);
void unlock(void);

// Timer Channel 5 Interrupt Service Routine
void interrupt 13 handler13() {
    tone(pitch);
}

// SCI0 Interrupt Service Routine
void interrupt 20 handler20() {
    // Store the read data in a queue.
    qstore(read_SCI0_Rx());
}

void main(void) {
    PLL_init();
    initq();
    SCI0_int_init(SERIAL0_BAUD_RATE);
    motor0_init();
    motor1_init();
    motor2_init();
    
    DDRB = RELAY_PIN;
    PORTB = RELAY_PIN;
    
    power_mode();
    
    while (1) {
        // If there exists any character in the serial buffer queue, process it.
        while (!qempty()) {
            // Store the receieved character.
            c = getq();
            
            switch(c) {
                // Since the key is not in the system, alert user.
                case '0':
                    lock();
                    auth_failed();
                    break;
                // Since the key is in the system, welcome them.
                case '1':
                case '2':
                    unlock();
                    break;
            }
            
            // Waits for the Raspberry Pi to signal for the system to continue.
            while (c != 'c') {
                while (qempty());
                c = getq();
            }
            
            // Lock the door.
            lock();
        }
    }
}

/*
 * Enable power mode on the system.
 */
void power_mode(void) {
    motor0(511);
    motor1(511);
    motor2(0);
}

/*
 * When the key has successfully authenticated, alert the user.
 */
void auth_success(void) {
    // Roughly 1000Hz
    pitch = 750;
    
    // Turn off red and blue LEDs.
    motor0(511);
    motor2(511);
   
    // Initialize the piezo.
    sound_init();
    
    // Blink the green LED and make tone on piezo three times.
    for (x = 0; x < 3; x++) {
        sound_on();
        motor1(0);
        ms_delay(100);
        sound_off();
        motor1(511);
        ms_delay(100);
    }
  
    // Display the power mode status.
    power_mode();
}

/*
 * When the key has failed authentication, alert the user.
 */
void auth_failed(void) {
    // Roughly 500Hz
    pitch = 1500;
    
    // Turn off green and blue LEDs.
    motor1(511);
    motor2(511);
   
    // Initialize the piezo.
    sound_init();
    
    // Blink the red LED and make tone on piezo three times.
    for (x = 0; x < 3; x++) {
        sound_on();
        motor0(0);
        ms_delay(100);
        sound_off();
        motor0(511);
        ms_delay(100);
    }
  
    // Display the power mode status.
    power_mode();
}

/*
 * Lock the door by deactivating the relay. Since the relay is low active, it is deactivated by setting PB4 high.
 */
void lock(void) {
    // Reset tick count.
    ticks = 0;
    
    // Turn off relay.
    PORTB |= RELAY_PIN;
}

/*
 * Unlock the door by activating the relay. Since the relay is low active, it is activated by setting PB4 low.
 */
void unlock(void) {
    // Turn on relay.
    PORTB &= ~RELAY_PIN;
    
    // Display success.
    auth_success();
}
