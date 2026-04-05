import sqlite3

def test_connection():
    try:
        # 1. Establish a connection to the database file
        conn = sqlite3.connect('hospital.db')
        
        # 2. Create a cursor object to execute SQL commands
        cursor = conn.cursor()

        # 3. Execute a simple SELECT query
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        
        # 4. Fetch all table names
        tables = cursor.fetchall()

        print("Connection Successful! Here are the tables in your database:")
        for table in tables:
            print(table[0])

        # 5. Close the connection
        conn.close()

    except sqlite3.Error as error:
        print("Failed to connect to SQLite:", error)

if __name__ == "__main__":
    test_connection()