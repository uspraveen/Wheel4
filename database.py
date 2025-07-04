# database.py

import sqlite3
import datetime

DATABASE_FILE = "glass_memory.db"

def initialize_database():
    """Connects to the DB and creates tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Create table to store transcripts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            speaker TEXT,
            text TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_transcription(speaker, text):
    """Saves a new piece of transcribed text to the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO transcripts (timestamp, speaker, text) VALUES (?, ?, ?)",
                   (timestamp, speaker, text))

    conn.commit()
    conn.close()

def get_all_transcripts():
    """Retrieves all transcripts to provide context to the AI."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT speaker, text FROM transcripts ORDER BY timestamp ASC")
    rows = cursor.fetchall()

    conn.close()
    return rows
