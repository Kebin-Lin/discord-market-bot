import os, atexit
from datetime import datetime
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

def addListing(marketID, listerID, itemName, price, notes, tags):
    if len(tags) > 10: # Too many tags
        return False
    cursor.execute("SELECT * FROM listings WHERE marketID = %s & listerID = %s LIMIT 10", (marketID, listerID,))
    if len(cursor.fetchall() == 10): # Too many existing listings
        return False
    cursor.execute(
        '''
        INSERT INTO listings (marketID, listerID, itemName, price, notes, tags)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING listingID
        ''',
        (marketID, listerID, itemName, price, notes, tuple(tags),)
    )
    return True

def removeListing(listingID):
    cursor.execute("DELETE FROM listings WHERE listingID = %s", (listingID,))
    return cursor.rowcount == 1

def search(marketID, query):
    cursor.execute(
        '''
        SELECT * FROM listings
        WHERE
            marketID = %s AND (
                itemName ILIKE %s OR
                notes ILIKE %s
            )
        LIMIT 10
        ''',
        (marketID, query, query,)
    )
    return cursor.fetchall()

def tagsearch(marketID, tags):
    if len(tags) > 10: # Too many tags
        return False
    cursor.execute(
        '''
        SELECT * FROM listings
        WHERE
            marketID = %s AND
            tags @> %s
        LIMIT 10
        ''',
        (marketID, tuple(tags),)
    )
    return cursor.fetchall()

@atexit.register
def saveChanges():
    conn.commit()
    cursor.close()