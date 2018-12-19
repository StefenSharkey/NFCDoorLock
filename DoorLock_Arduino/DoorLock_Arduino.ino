/* NFC Door Lock - Arduino Code
 * Author: Stefen Sharkey
 * Date: December 6, 2017
 * School: Monroe Community College
 * Course: Computer Science 202 - Embedded Programming in C and Assembly
 * Professor: George Fazekas
 */

#include <LiquidCrystal_I2C.h>
#include "Adafruit_PN532.h"
#include "SPI.h"

#if defined(ARDUINO_ARCH_SAMD)
    // for Zero, output on USB Serial console, remove line below if using programming port to program the Zero!
    // also change #define in Adafruit_PN532.cpp library file
    #define Serial SerialUSB
#endif

#define SLAVE_ADDRESS 0x04

#define PN532_IRQ   (2)
#define PN532_RESET (3)

#define BAUD_RATE 115200

#define LCD_WIDTH 16
#define LCD_ROWS 2

Adafruit_PN532 nfc(PN532_IRQ, PN532_RESET);
LiquidCrystal_I2C lcd(0x27, 2, 1, 0, 4, 5, 6, 7, 3, POSITIVE);  // Set the LCD I2C address

bool programming = false;
bool deleting = false;

void setup() {
    // Enable serial input and output at 115200 baud rate.
    Serial.begin(BAUD_RATE);

    // Enable the LCD 
    lcd.begin(LCD_WIDTH, LCD_ROWS);

    // NFC setup
    nfc.begin();
  
    // Obtain various information about attached NFC shield.
    // Returns 0 if no board is attached.
    uint32_t versiondata = nfc.getFirmwareVersion();
    
    // If the board is not attached, notify the user via the LCD and do nothing forever.
    if (!versiondata) {
        lcd.setCursor(0, 0);
        lcd.print("Error: Didn't");
        lcd.setCursor(0, 1);
        lcd.print("find PN53x board");
      while (1); // halt
    }
    
    nfc.SAMConfig();
}

void loop(void) {
    // If the system isn't programming, nor deleting, welcome the user.
    // If the system is programming or deleting, turn thieir respective modes on.
    if (!programming && !deleting) {
        lcd.setCursor(0, 0);
        lcdPrintCenter(lcd, "Welcome to");
        lcd.setCursor(0, 1);
        lcdPrintCenter(lcd, "Sharkey's home.");
    } else if (programming) {
        programmingModeOn();
    } else if (deleting) {
        deletingModeOn();
    }

    // Get the card ID.
    uint32_t card_id = getCard();

    // Send card ID via serial.
    Serial.println(card_id);

    if (programming) {
        // If the system is programming, wait for success code.
        bool success = getSerialInput().toInt();

        // Display the success or failure message on the LCD.
        if (success) {
            lcd.clear();
            lcd.print("Programmed key");
            lcd.setCursor(0, 1);
            lcd.print(card_id);
        } else {
            lcd.clear();
            lcd.print("Key already in");
            lcd.setCursor(0, 1);
            lcd.print("in system.");
        }

        // Turn off the programming mode.
        programming = false;
    } else if (deleting) {
        // If the system is deleting, wait for success code.
        bool success = getSerialInput("Is success?").toInt();

        // Display the success or failure message on the LCD.
        if (success) {
            lcd.clear();
            lcd.print("Deleted key");
            lcd.setCursor(0, 1);
            lcd.print(card_id);
        } else {
            lcd.clear();
            lcd.print("Key not in");
            lcd.setCursor(0, 1);
            lcd.print("system.");
        }

        // Turn off the deleting mode.
        deleting = false;
    } else {
        // If the system is not programming, nor deleting, wait for command from the Raspberry Pi.
        int rank = getSerialInput("Please wait...").toInt();
    
        switch(rank) {
            // Since the key is not in the system, alert user.
            case 0: {
                    lcd.clear();
                    lcd.print("Error: Key not");
                    lcd.setCursor(0, 1);
                    lcd.print("valid.");
                }
                break;
            // Since the key is in the system, welcome them.
            case 1:
            case 2: {
                    String name = getSerialInput("Enter name...");
    
                    lcd.clear();
                    lcdPrintCenter(lcd, "Welcome");
                    lcd.setCursor(0, 1);
                    lcdPrintCenter(lcd, name);
                }
                break;
            // Wipe the system.
            case 3: {
                    lcd.clear();
                    lcdPrintCenter(lcd, "Wiping system...");
                }
                break;
            // Turn on the programming mode.
            case 4:
                programmingModeOn();
                break;
            // Turn on the deleting mode.
            case 5:
                deletingModeOn();
                break;
        }
    }
    
    // Waits for the Raspberry Pi to signal for the system to continue.
    String buffer;
    while (buffer.charAt(0) != 'c') {
        buffer = getSerialInput();
    }
}

/*!
 * Function overload for getSerialInput(String).
 */
String getSerialInput() {
    return getSerialInput("");
}

/*!
 * Waits for and returns any serial input. Allows for waiting text to be printed to the LCD.
 * 
 * @param       waitText    Text to be printed to LCD while the Arduino is waiting for serial data.
 */ 
String getSerialInput(String waitText) {
    // If there is waiting text, print it to the LCD.
    if (waitText.length() > 0) {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcdPrintCenter(lcd, waitText);
    }
    
    // Wait for serial input.
    while (Serial.available() == 0);

    // Delay to allow all serial input to be received.
    delay(10);

    // Buffer to hold parsed serial data.
    String buffer = "";
    
    // Read serial data and feed it to the buffer while serial data exists.
    while (Serial.available() > 0) {
        char c = Serial.read();
        buffer += c;
    }

    //return buffer.substring(0, buffer.length() - 2);
    return buffer;
}

/*!
 * Prints centered text to the LCD by adding padding around the text. Supports both odd and even text length.
 * 
 * @param       lcd     LCD to which the text is printed.
 * @param       text    Text to be centered.
 */
void lcdPrintCenter(LiquidCrystal_I2C lcd, String text) {
    // TODO: Add whitespace trimming feature.
    
    if (text.length() < LCD_WIDTH) {
        int space;

        if (text.length() & 0x01) {
            // Odd length
            space = (LCD_WIDTH - text.length() + 1) / 2;
        } else {
            // Even length
            space = (LCD_WIDTH - text.length()) / 2;
        }
        
        for (int x = 0; x < space; x++) {
            text = " " + text + " ";
        }
    }
    
    lcd.print(text);
}

/*!
 * Returns the card ID of any NFC card read by the PN532 NFC reader.
 */
uint32_t getCard(){
    uint8_t success;
    
    // Buffer to store the returned UID.
    uint8_t uid[] = {0, 0, 0, 0};
    uint8_t uidLength;
    uint32_t cardId = 0;
    
    // Waits until an NFC chip is read by the PN532.
    success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
  
    // If the PN532 successfully read a chip, return the card ID.
    if (success) {
        cardId |= uid[3];
        
        for (int i = uidLength - 2; i >= 0; i--) {
            cardId <<= 8;
            cardId |= uid[i];
        }

        return cardId;
    }

    return 0;
}

/*!
 * Enables the programming mode.
 */
void programmingModeOn() {
    programming = true;
    
    lcd.clear();
    lcd.print("Programming mode");
    lcd.setCursor(0, 1);
    lcd.print("enabled.");
}

/*!
 * Enables the deleting mode.
 */
void deletingModeOn() {
    deleting = true;
    
    lcd.clear();
    lcd.print("Deleting mode");
    lcd.setCursor(0, 1);
    lcd.print("enabled.");
}
