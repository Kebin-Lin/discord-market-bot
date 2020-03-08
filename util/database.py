import os, atexit
from datetime import timedelta
from timeloop import Timeloop
import psycopg2

tl = Timeloop()
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

def isAdmin(marketID, memberID):
    cursor.execute("SELECT isadmin FROM members WHERE marketID = %s AND memberID = %s LIMIT 1", (marketID, memberID,))
    if cursor.rowcount == 0:
        return False
    return cursor.fetchall()[0][0]

def isOwner(marketID, userID):
    cursor.execute("SELECT 1 FROM markets WHERE marketID = %s AND ownerID = %s LIMIT 1", (marketID, userID,))
    if cursor.rowcount == 0:
        return False
    return cursor.fetchall()[0][0]

def changePublic(marketID, public):
    cursor.execute("UPDATE markets SET public = %s WHERE marketID = %s", (public, marketID,))

def isPublic(marketID):
    cursor.execute("SELECT public FROM markets WHERE marketID = %s LIMIT 1", (marketID,))
    if cursor.rowcount == 0:
        return False
    return cursor.fetchall()[0][0]

def isMember(marketID, memberID):
    cursor.execute("SELECT 1 FROM members WHERE marketID = %s and memberID = %s LIMIT 1", (marketID, memberID,))
    return cursor.rowcount == 1

def removeMember(marketID, memberID):
    cursor.execute("DELETE FROM members WHERE marketID = %s AND memberID = %s", (marketID, memberID,))
    return cursor.rowcount == 1

def updateMember(marketID, memberID, isadmin = False):
    cursor.execute(
        '''
        INSERT INTO members (marketID, memberID, isadmin)
        VALUES (%s, %s, %s)
        ON CONFLICT ON CONSTRAINT unq_marketID_memberID
        DO UPDATE SET isadmin = %s;
        ''',
        (marketID, memberID, isadmin, isadmin)
    )

def createMarket(marketID, ownerID, public = False):
    cursor.execute("SELECT 1 FROM markets WHERE marketID = %s LIMIT 1", (marketID,))
    if cursor.rowcount != 0:
        return False
    cursor.execute(
        '''
        INSERT INTO markets (marketID, ownerID, public)
        VALUES (%s, %s, %s)
        ''',
        (marketID, ownerID, public,)
    )
    return True

def addListing(marketID, listerID, itemName, price, notes):
    cursor.execute("SELECT 1 FROM listings WHERE marketID = %s AND listerID = %s LIMIT 15", (marketID, listerID,))
    if len(cursor.fetchall()) == 15: # Too many existing listings
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
    cursor.execute("SELECT * FROM listings WHERE marketID = %s AND listerID = %s LIMIT 30", (marketID, listerID,))
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
    cursor.execute('SELECT 1 FROM markets WHERE marketID = %s', (marketID,))
    if cursor.rowcount == 0:
        return False
    cursor.execute( #Upsert
        '''
        INSERT INTO channelLinks (channelID, marketID)
        VALUES (%s, %s)
        ON CONFLICT (channelID)
        DO UPDATE SET marketID = %s;
        ''',
        (channelID, marketID, marketID,)
    )
    return True

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