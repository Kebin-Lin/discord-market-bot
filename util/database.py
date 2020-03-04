import os, atexit
from datetime import timedelta
from timeloop import Timeloop
import psycopg2

tl = Timeloop()
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

def addListing(marketID, listerID, itemName, price, notes):
    cursor.execute("SELECT * FROM listings WHERE marketID = %s AND listerID = %s LIMIT 10", (marketID, listerID,))
    if len(cursor.fetchall()) == 30: # Too many existing listings
        return False
    cursor.execute(
        '''
        INSERT INTO listings (marketID, listerID, itemName, price, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING listingID
        ''',
        (marketID, listerID, itemName, price, notes,)
    )
    return True

def removeListing(listingID):
    cursor.execute("DELETE FROM listings WHERE listingID = %s", (listingID,))
    return cursor.rowcount == 1

def getListings(marketID, listerID):
    cursor.execute("SELECT * FROM listings WHERE marketID = %s AND listerID = %s", (marketID, listerID,))
    return cursor.fetchall()

def search(marketID, query):
    formattedQuery = f"%{query}%"
    cursor.execute(
        '''
        SELECT * FROM listings
        WHERE
            marketID = %s AND
            (itemName ILIKE %s OR notes ILIKE %s)
        ORDER BY
            price ASC,
            timeAdded ASC
        LIMIT 100
        ''',
        (marketID, formattedQuery, formattedQuery,)
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

@tl.job(interval = timedelta(hours = 1))
def expireAndCommit():
    print('Expiring old listings and committing to the database...')
    cursor.execute('SELECT expireRows()')
    conn.commit()
    print('Expire and commit complete.')

@atexit.register
def saveChanges():
    conn.commit()
    cursor.close()

tl.start()