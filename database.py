#!/usr/bin/env python3
"""
Wheel4 - Database Management
SQLite for API keys and session history
"""

import sqlite3
import datetime
import os

DB_FILE = "ai_brain.db"

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_FILE)

def initialize_database():
    """Initialize database tables"""
    print("🗃️  Initializing database...")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # API Keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY,
                api_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT
            )
        ''')
        
        # Interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        
        conn.commit()
    
    print("✅ Database tables ready")

def save_api_key(api_key):
    """Save or update API key"""
    timestamp = datetime.datetime.now().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if key exists
        cursor.execute("SELECT id FROM api_keys LIMIT 1")
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE api_keys SET api_key = ?, updated_at = ? WHERE id = ?",
                (api_key, timestamp, existing[0])
            )
            print("🔑 API key updated")
        else:
            cursor.execute(
                "INSERT INTO api_keys (api_key, created_at, updated_at) VALUES (?, ?, ?)",
                (api_key, timestamp, timestamp)
            )
            print("🔑 API key saved")
        
        conn.commit()

def get_api_key():
    """Get current API key"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT api_key FROM api_keys ORDER BY updated_at DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None

def create_new_session():
    """Create a new session"""
    timestamp = datetime.datetime.now().isoformat()
    session_name = f"Session {timestamp[:19]}"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (created_at, name) VALUES (?, ?)",
            (timestamp, session_name)
        )
        session_id = cursor.lastrowid
        conn.commit()
    
    print(f"📝 Created session {session_id}: {session_name}")
    return session_id

def save_interaction(session_id, question, response):
    """Save a question-response interaction"""
    timestamp = datetime.datetime.now().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO interactions (session_id, timestamp, question, response) VALUES (?, ?, ?, ?)",
            (session_id, timestamp, question, response)
        )
        conn.commit()
    
    print(f"💾 Saved interaction for session {session_id}")

def get_session_history(session_id, limit=20):
    """Get recent interactions from a session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT question, response, timestamp FROM interactions WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
        return list(reversed(cursor.fetchall()))  # Return in chronological order

def close_session(session_id):
    """Mark a session as closed"""
    timestamp = datetime.datetime.now().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Add closed_at column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN closed_at TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        cursor.execute(
            "UPDATE sessions SET closed_at = ? WHERE id = ?",
            (timestamp, session_id)
        )
        conn.commit()
    
    print(f"📝 Session {session_id} marked as closed")

def get_all_sessions():
    """Get all sessions"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, created_at FROM sessions ORDER BY created_at DESC")
        return cursor.fetchall()

def get_session_stats(session_id):
    """Get statistics for a session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) as interaction_count FROM interactions WHERE session_id = ?",
            (session_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else 0