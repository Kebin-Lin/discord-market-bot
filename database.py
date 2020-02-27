import os, atexit
from datetime import datetime
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

def setup():
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS listings(
            listingID SERIAL PRIMARY KEY,
            server TEXT NOT NULL,
            listerID TEXT NOT NULL,
            itemName VARCHAR(64) NOT NULL,
            price NUMERIC NOT NULL,
            notes TEXT,
            timeAdded TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS tags(
            server TEXT NOT NULL,
            listingID SERIAL REFERENCES listings(listingID) ON DELETE CASCADE,
            tag VARCHAR(32) NOT NULL
        )
        '''
    )
    cursor.execute(
        '''
        CREATE OR REPLACE FUNCTION expireRows() RETURNS void AS $$
            BEGIN
                DELETE FROM listings WHERE timeAdded < NOW() - INTERVAL '3 days';
            END;
        $$
        LANGUAGE plpgsql;
        '''
    )

setup()

def addListing(server, listerID, itemName, price, notes, tags):
    if len(tags) > 10: # Too many tags
        return False
    cursor.execute("SELECT * FROM listings WHERE server = %s & listerID = %s LIMIT 10", (server, listerID,))
    if len(cursor.fetchall() == 10): # Too many existing listings
        return False
    cursor.execute(
        '''
        INSERT INTO listings (server, listerID, itemName, price, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING listingID
        ''',
        (server, listerID, itemName, price, notes,)
    )
    listingID = cursor.fetchone()[0]
    for i in tags:
        cursor.execute("INSERT INTO tags (server, listingID, tag) VALUES (%s, %s, %s)", (server, listingID, i,))

def removeListing(listingID):
    cursor.execute("DELETE FROM listings WHERE listingID = %s", (listingID,))

@atexit.register
def saveChanges():
    conn.commit()
    cursor.close()