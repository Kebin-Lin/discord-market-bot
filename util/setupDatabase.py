import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = conn.cursor()

def setup():
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS listings(
            listingID SERIAL PRIMARY KEY,
            marketID VARCHAR(64) NOT NULL,
            listerID NUMERIC NOT NULL,
            itemName VARCHAR(64) NOT NULL,
            price NUMERIC NOT NULL,
            notes VARCHAR(300),
            timeAdded TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS channelLinks(
            channelID NUMERIC UNIQUE NOT NULL,
            marketID VARCHAR(64) NOT NULL
        )
        '''
    )
    cursor.execute(
        '''
        CREATE OR REPLACE FUNCTION expireRows() RETURNS void AS $$
            BEGIN
                DELETE FROM listings WHERE timeAdded < NOW() - INTERVAL '7 days';
            END;
        $$
        LANGUAGE plpgsql;
        '''
    )
    cursor.execute(
        '''
        CREATE EXTENSION IF NOT EXISTS pg_trgm;
        CREATE INDEX IF NOT EXISTS nameIndex ON listings USING gin (itemName gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS notesIndex ON listings USING gin (notes gin_trgm_ops);
        '''
    )

setup()
conn.commit()
cursor.close()