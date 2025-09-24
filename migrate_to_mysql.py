import pandas as pd
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables from a .env file for local development
load_dotenv()

# --- Configuration ---
EXCEL_FILE = "RamzatCheckIN-2025-Deval-22-Sep-OK.xlsx"
DATABASE_SHEET = "Database"
BARCODE_COLUMN = "Barcode"

# --- Aiven MySQL Configuration for Migration ---
# Credentials are now read from environment variables (.env file)
DB_CONFIG = {
    'host': os.environ.get('RDS_HOSTNAME'),
    'user': os.environ.get('RDS_USERNAME'),
    'password': os.environ.get('RDS_PASSWORD'),
    'database': os.environ.get('RDS_DB_NAME'),
    'port': 24059
}

def migrate_data():
    """Reads barcodes from an Excel file and inserts them into your Aiven MySQL database."""
    
    # Check for missing essential variables first
    if not all([DB_CONFIG['host'], DB_CONFIG['user'], DB_CONFIG['password'], DB_CONFIG['database'], DB_CONFIG['port']]):
        print("---")
        print("ERROR: Database environment variables are not set in your .env file.")
        print("Please set RDS_HOSTNAME, RDS_USERNAME, RDS_PASSWORD, RDS_DB_NAME, and RDS_PORT.")
        print("---")
        return

    conn = None
    try:
        # 1. Connect to the database
        print("Connecting to the Aiven MySQL database...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Connection successful.")

        # 2. Create the 'barcodes' table if it doesn't exist
        print("Creating 'barcodes' table if it doesn't exist...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS barcodes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                barcode VARCHAR(255) NOT NULL UNIQUE
            )
        """)
        print("'barcodes' table is ready.")

        # 3. Read barcodes from the Excel file
        print(f"Reading barcodes from '{EXCEL_FILE}'...")
        db_df = pd.read_excel(EXCEL_FILE, sheet_name=DATABASE_SHEET)
        barcodes = db_df[BARCODE_COLUMN].dropna().unique()
        print(f"Found {len(barcodes)} unique barcodes to migrate.")

        # 4. Insert barcodes into the database
        # Using INSERT IGNORE to prevent errors if a barcode already exists
        insert_barcode_query = "INSERT IGNORE INTO barcodes (barcode) VALUES (%s)"
        
        barcode_list = [(str(b),) for b in barcodes]
        cursor.executemany(insert_barcode_query, barcode_list)
        
        conn.commit()
        print(f"Successfully migrated {cursor.rowcount} new barcodes into the database.")

    except FileNotFoundError:
        print(f"Error: The file '{EXCEL_FILE}' was not found. Please make sure it's in the same directory.")
    except KeyError:
        print(f"Error: The '{DATABASE_SHEET}' sheet must contain a '{BARCODE_COLUMN}' column.")
    except Error as e:
        print(f"Database error during migration: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    print("Starting data migration from Excel to Aiven MySQL...")
    migrate_data()
    print("Migration process finished.")
