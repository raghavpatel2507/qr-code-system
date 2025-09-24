import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.environ.get('RDS_HOSTNAME'),
    'user': os.environ.get('RDS_USERNAME'),
    'password': os.environ.get('RDS_PASSWORD'),
    'database': os.environ.get('RDS_DB_NAME'),
    'port': 24059
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("SELECT * FROM barcodes LIMIT 10;")
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()
