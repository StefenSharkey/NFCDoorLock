'''
 * NFC Door Lock - Raspberry Pi Code
 * Author: Stefen Sharkey
 * Date: December 6, 2017
 * School: Monroe Community College
 * Course: Computer Science 202 - Embedded Programming in C and Assembly
 * Professor: George Fazekas
'''

from enum import IntEnum
import serial
import sqlite3
import struct
import time
import traceback

ser_ard = serial.Serial('/dev/ttyACM0', 115200)
ser_tb = serial.Serial('/dev/ttyUSB0', 9600)
db_conn = sqlite3.connect(r'/home/pi/Documents/doorlock.db')
c = db_conn.cursor()

def __main__():
    programming = False
    deleting = False
    
    try:
        # Create the CardID table if it doesn't already exist.
        c.executescript('''CREATE TABLE IF NOT EXISTS CardIDs (
                              'CardID'   INT PRIMARY KEY NOT NULL,
                              'Rank'     INT             NOT NULL,
                              'Name'     TEXT,
                              'LastUsed' DATETIME
                           );
                           CREATE TABLE IF NOT EXISTS UsageLog (
                              'Time'   DATETIME PRIMARY KEY NOT NULL,
                              'CardID' INT                  NOT NULL,
                              'Rank'   INT                  NOT NULL
                           );''')
        
        # Add default cards to database if they don't exist.
        addDefaultCards()
        
        #ser_ard.write(b'0')
        
        while True:
            print("Ready to receive input.")
            
            # Stores the raw incoming serial mesage from the Arduino.
            raw_rx_ard = ser_ard.readline().decode('utf-8')
            #raw_rx_ard = '721416196'
            
            print('Received input:', raw_rx_ard)
            
            # Ensures the serial message is usable.
            if len(raw_rx_ard) > 2:
                # Strips the incoming serial message of carriage return and newline characters
                rx_ard = raw_rx_ard[:-2]
                
                print('Received usable input:', rx_ard)
                
                # Check if serial message was a card ID.
                #if len(rx_ard) >= 9:
                if len(rx_ard) >= 9:
                    # Store the received card ID.
                    #card_id = int(rx_ard)
                    card_id = int(rx_ard)
                    
                    print('Input was a card:', card_id)
                    
                    # Holds the card rank, defaulting to unknown.
                    card_rank = 0
                    
                    # Obtains the card's rank from the database.
                    c.execute('SELECT Rank FROM CardIDs WHERE CardID IS {};'.format(card_id))
                    
                    # Holds the first entry that the previous SQLite command returned.
                    db_query = c.fetchone()
                    
                    # Checks if the card exists in the database.
                    if db_query is not None:
                        # Sets the card rank to what the database holds.
                        card_rank = db_query[0]
                        
                        # Sets the card's last used time in the database.
                        c.execute('UPDATE CardIDs SET LastUsed = datetime(\'now\') WHERE CardID IS {};'.format(card_id))
                    
                    print('Card rank is', card_rank)
                    
                    # If the system is not programmor, nor deleting, send the Arduino and Thunderbird the card rank.
                    if not programming and not deleting:
                        print('Sending Arduino card rank.')
                        
                        # Send the card rank to Arduino and Thunderbird.
                        card_rank_bytes = str(card_rank).encode()
                        ser_ard.write(card_rank_bytes)
                        ser_tb.write(card_rank_bytes)
                    
                    if programming:
                        # If the system is programming and an unknown card is read, add it to the system and signal the Arduino and Thunderbird.
                        if card_rank == Rank.unknown.value:
                            print('programming new card: {}'.format(card_id))
                            c.execute('INSERT INTO CardIDs VALUES ({}, 1, NULL, NULL);'.format(card_id))
                            ser_ard.write(b'1')
                        else:
                            ser_ard.write(b'0')
                            
                        ser_tb.write(b'4')
                        programming = False
                    elif deleting:
                        # If the system is deleting and a normal user card is read, remove it from the system and signal the Arduino and Thunderbird.
                        if card_rank == Rank.user.value:
                            print('Deleting card: {}'.format(card_id))
                            c.execute('DELETE FROM CardIDs WHERE CardID IS {};'.format(card_id))
                            ser_ard.write(b'1')
                        else:
                            ser_ard.write(b'0')
                        
                        ser_tb.write(b'5')
                        deleting = False
                    elif card_rank == Rank.wipe.value:
                        print('Wiping card database...')
                        c.executescript('DELETE FROM CardIDs; VACUUM;')
                    elif card_rank == Rank.master.value:
                        print('Master card detected. Reprogramming database.')
                        addDefaultCards()
                    
                    # Toggle deleting or programming modes.
                    if not deleting and card_rank == Rank.programming.value:
                        programming = not programming
                    elif not programming and card_rank == Rank.delete.value:
                        deleting = not deleting
                    
                    # Adds the usage to usage log table.
                    c.execute('INSERT INTO "UsageLog" VALUES (datetime(\'now\'), {}, {})'.format(card_id, card_rank))
                    
                    # Send the Arduino the card's name.
                    if card_rank == Rank.user.value or card_rank == Rank.administrator.value:
                        # Obtains the card's name from the database.
                        c.execute('SELECT Name FROM CardIDs WHERE CardID IS {};'.format(card_id))
                        
                        db_query = c.fetchone()
                        
                        # Set the card name to the card ID in case no name exists in the database.
                        card_name = card_id
                        
                        # If a name exists in the database, set the card name to it.
                        if db_query is not None and db_query[0] is not None:
                            card_name = db_query[0]
                        
                        print('Card name:', card_name)
                        
                        time.sleep(0.05)
                        
                        # Send the card name to the Arduino.
                        ser_ard.write(str(card_name).encode())
            time.sleep(5)
            
            ser_ard.write(b'c')
            ser_tb.write(b'c')
    except Exception as e:
        # Print the exception.
        #print("Exception: {}".format(e))
        traceback.print_exc()

        # Close the serial line.
        ser_ard.close()
        ser_tb.close()
    
# Checks if each query exists in the table.
# TODO: Figure out if SQLite supports the following with a single execution statement per query.
def addDefaultCards():
    # Check for Stefen's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardID IS 721416196;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (721416196, 2, 'Stefen Sharkey', NULL);")
        
    # Check for Master Wiper's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardID IS 704852996;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (704852996, 3, 'Master Wiper', NULL);")
        
    # Check for Master Programming's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardID IS 711223556;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (711223556, 4, 'Master Programming', NULL);")
        
    # Check for Master Deletion's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardID IS 709711364;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (709711364, 5, 'Master Deletion', NULL);")
        
    # Check for Master Card's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardID IS 707829764;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (707829764, 6, 'Master Card', NULL);")

class Rank(IntEnum):
    unknown = 0
    user = 1
    administrator = 2
    wipe = 3
    programming = 4
    delete = 5
    master = 6

__main__()