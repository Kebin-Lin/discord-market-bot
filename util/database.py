import os, atexit
from datetime import datetime
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

def addListing(marketID, listerID, itemName, price, notes, tags):
    cursor.execute("SELECT * FROM listings WHERE marketID = %s AND listerID = %s LIMIT 10", (marketID, listerID,))
    if len(cursor.fetchall()) == 32: # Too many existing listings
        return False
    cursor.execute(
        '''
        INSERT INTO listings (marketID, listerID, itemName, price, notes, tags)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING listingID
        ''',
        (marketID, listerID, itemName, price, notes, tags,)
    )
    return True

def removeListing(listingID):
    cursor.execute("DELETE FROM listings WHERE listingID = %s", (listingID,))
    return cursor.rowcount == 1

def getListings(marketID, listerID):
    cursor.execute("SELECT * FROM listings WHERE marketID = %s AND listerID = %s", (marketID, listerID,))
    return cursor.fetchall()

def search(marketID, query):
    cursor.execute(
        '''
        SELECT * FROM listings
        WHERE
            marketID = %s AND 
            (itemName ILIKE %s OR notes ILIKE %s)
        LIMIT 10
        ''',
        (marketID, query, query,)
    )
    return cursor.fetchall()

def tagsearch(marketID, tags):
    cursor.execute(
        '''
        SELECT * FROM listings
        WHERE
            marketID = %s AND
            tags @> %s
        LIMIT 10
        ''',
        (marketID, tags,)
    )
    return cursor.fetchall()

def setMarket(channelID, marketID):
    cursor.execute( #Upsert
        '''
        INSERT INTO channelLinks (channelID, marketID)
        VALUES (%s, %s)
        ON CONFLICT (channelID)
        DO UPDATE SET marketID = %s;
        ''',
        (channelID, marketID, marketID,)
    )

def getMarket(channelID):
    cursor.execute(
        '''
        SELECT marketID FROM channelLinks WHERE channelID = %s LIMIT 1
        ''',
        (channelID,)
    )
    output = cursor.fetchone()
    if output == None:
        return None
    return output[0]

@atexit.register
def saveChanges():
    conn.commit()
    cursor.close()