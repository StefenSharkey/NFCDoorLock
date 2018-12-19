'''
 * NFC Door Lock - Raspberry Pi Code
 * Author: Stefen Sharkey
 * Date: December 6, 2017
 * School: Monroe Community College
 * Course: Computer Science 202 - Embedded Programming in C and Assembly
 * Professor: George Fazekas
'''

from enum import IntEnum
import re
import serial
import sqlite3
import traceback

ser = serial.Serial('/dev/ttyACM0', 115200)
conn = sqlite3.connect('/srv/nfcdoorlock.db')
c = conn.cursor()

def __main__():
    sendCard = False

    deleting = False
    learning = False

    deletingCard = 0

    last_used = 'LastUsed'
    
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

        # Akin to Arduino's loop().
        while True:
            # Stores the raw incoming serial message.
            raw_rx = ser.readline().decode("utf-8")

            # Ensures the serial message is usable.
            if len(raw_rx) > 2:
                # Read the incoming serial messages from the Arduino.
                rx = raw_rx[:-2]
                print("Arduino: " + rx)

                # Check if the the Arduino is transmitting a card ID.
                if rx[:9] == "Card ID: ":
                    # Holds the transmitted card ID.
                    cardId = int(rx[9:])

                    # Holds the card rank. Initialized to zero in case card is not found.
                    cardRank = 0

                    # Obtains the card's rank from the database.
                    c.execute('SELECT Rank FROM CardIDs WHERE CardId IS {};'.format(cardId))

                    # Holds the first entry the previous SQL command returned.
                    # Note: If nothing was returned, then type(dbInfo) is None.
                    dbInfo = c.fetchone()

                    # Checks if the card exists in the database.
                    if dbInfo is not None:
                        # Sets the card rank to whatever the database holds.
                        cardRank = dbInfo[0]
                        
                        # Sets the card's last used time in the database.
                        c.execute('UPDATE CardIDs SET LastUsed = datetime(\'now\') WHERE CardID IS {};'.format(cardId))

                    # Toggle deleting or learning modes.
                    if not deleting and cardRank == Rank.programming.value:
                        learning = not learning
                    elif not learning and cardRank == Rank.delete.value:
                        deleting = not deleting
                        
                        # TODO: Figure out why I put this here...
                        deletingCard = cardId

                    if learning and cardRank == Rank.unknown.value:
                        print('RPi: Learning new card: {}'.format(cardId))
                        c.execute('INSERT INTO CardIDs VALUES ({}, 1, NULL, NULL);'.format(cardId))
                    elif deleting and cardRank > 0 and cardId != deletingCard:
                        print('RPi: Deleting card: {}'.format(cardId))
                        c.execute('DELETE FROM CardIDs WHERE CardID IS {};'.format(cardId))
                    elif cardRank == Rank.wipe.value:
                        print('RPi: Wiping card database...')
                        c.executescript('DELETE FROM CardIDs; VACUUM;')
                    elif cardRank == Rank.master.value:
                        print('RPi: Master card detected. Relearning database.')
                        addDefaultCards()

                    # Adds the usage to the usage log table.
                    c.execute('INSERT INTO "UsageLog" VALUES (datetime(\'now\'), {}, {})'.format(cardId, cardRank))

                    # If true, writes the card ID to the serial buffer.
                    if sendCard:
                        ser.write(cardId.to_bytes(4, byteorder = 'big'))

                    # Writes the card rank to the serial buffer.
                    ser.write(int(cardRank).to_bytes(1, byteorder = 'big'))

                    # Commit all changes to the database file.
                    conn.commit()
    except Exception as e:
        # Print the exception.
        #print("Exception: {}".format(e))
        traceback.print_exc()

        # Close the serial line.
        ser.close()
        
# Checks if each query exists in the table.
# TODO: Figure out if SQLite supports the following with a single execution statement per query.
def addDefaultCards():
    # Check for Stefen's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardId IS 721416196;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (721416196, 2, 'Stefen Sharkey', NULL);")
        
    # Check for Master Wiper's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardId IS 704852996;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (704852996, 3, 'Master Wiper', NULL);")
        
    # Check for Master Programming's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardId IS 711223556;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (711223556, 4, 'Master Programming', NULL);")
        
    # Check for Master Deletion's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardId IS 709711364;')
    
    if c.fetchone() is None:
        c.execute("INSERT INTO CardIDs VALUES (709711364, 5, 'Master Deletion', NULL);")
        
    # Check for Master Card's card.
    c.execute('SELECT Rank FROM CardIDs WHERE CardId IS 707829764;')
    
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
