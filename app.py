from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

app = Flask(__name__)

# i add new code

# --- Database Configuration ---
# These will be set from environment variables on your hosting platform (e.g., Render)
DB_HOST = os.environ.get('RDS_HOSTNAME')
DB_USER = os.environ.get('RDS_USERNAME')
DB_PASSWORD = os.environ.get('RDS_PASSWORD')
DB_NAME = os.environ.get('RDS_DB_NAME')
db_port = 24059

def create_db_connection():
    """Create a database connection to the AWS RDS MySQL database."""
    # Check for missing essential variables first
    if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
        print("---")
        print("ERROR: Database environment variables are not set.")
        print("Please set RDS_HOSTNAME, RDS_USERNAME, RDS_PASSWORD, and RDS_DB_NAME.")
        print("For local testing, you can create a .env file or set them in your shell.")
        print("---")
        return None

    try:
        # Get port and convert to integer, defaulting to 3306
        db_port = int(os.environ.get('RDS_PORT', 3306))

        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=db_port,
            connection_timeout=5  # Add a 5-second connection timeout
        )
        return conn
    except ValueError:
        print(f"Error: Invalid port number provided for RDS_PORT.")
        return None
    except Error as e:
        # In a real app, you'd want more robust logging here
        print(f"Error connecting to MySQL database: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def check_barcode_page():
    """Renders a web page to check barcodes and handles form submission."""
    result = None
    barcode_to_check = ""

    if request.method == 'POST':
        barcode_to_check = request.form.get('barcode', '').strip()
        if barcode_to_check:
            conn = create_db_connection()
            if not conn:
                # In a real app, you might want to show an error page
                return "Error: Could not connect to the database", 500

            try:
                cursor = conn.cursor()
                query = "SELECT barcode FROM barcodes WHERE barcode = %s"
                cursor.execute(query, (barcode_to_check,))
                db_result = cursor.fetchone()

                if db_result:
                    result = "Valid"
                else:
                    result = "Invalid"
            except Error as e:
                print(f"Database query error: {e}")
                result = "Error"
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
    
    return render_template('index.html', result=result, barcode=barcode_to_check)

# The API endpoint is no longer the primary interface, but can be kept for other services.
@app.route('/check_barcode_api', methods=['POST'])
def check_barcode_api():
    """API endpoint to check if a barcode exists in the database."""
    data = request.get_json()
    if not data or 'barcode' not in data:
        return jsonify({"error": "Missing 'barcode' in request body"}), 400

    barcode_to_check = data['barcode']
    conn = create_db_connection()

    if not conn:
        return jsonify({"error": "Could not connect to the database"}), 500

    try:
        cursor = conn.cursor()
        query = "SELECT barcode FROM barcodes WHERE barcode = %s"
        cursor.execute(query, (barcode_to_check,))
        result = cursor.fetchone()

        if result:
            return jsonify({"status": "valid"})
        else:
            return jsonify({"status": "invalid"})

    except Error as e:
        print(f"Database query error: {e}")
        return jsonify({"error": "An error occurred while querying the database"}), 500
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# This is required for WSGI servers like Gunicorn to find the application
application = app

if __name__ == '__main__':
    # For local testing, you might need to set up environment variables
    # or a different connection method (e.g., a local database).
    app.run(debug=True)
