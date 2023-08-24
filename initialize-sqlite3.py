import sqlite3


# Connect to the SQLite database
connection = sqlite3.connect("database.db")
cursor = connection.cursor()

# Create a table if it doesn't exist
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS selected_books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        authors TEXT,
        year INTEGER,
        source TEXT,
        isbn INTEGER,
        searchTerms TEXT,
        selectionTimeUtc TEXT
    )
"""
)

# Commit the changes and close the connection
connection.commit()
connection.close()
