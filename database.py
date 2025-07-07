#!/usr/bin/env python3
"""
Wheel4 - Database Management  
Fixed custom instructions handling with proper session info queries
"""

import sqlite3
import datetime
import os
import json

DB_FILE = "ai_brain.db"
current_session_id = None

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_FILE)

def initialize_database():
    """Initialize database tables with migration support"""
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
        
        # Sessions table with enhanced fields including custom_instructions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                name TEXT,
                closed_at TEXT,
                total_tokens INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                custom_instructions TEXT DEFAULT ''
            )
        ''')
        
        # Check if columns exist and add them if not
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in columns:
            print("🔄 Adding is_active column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN is_active INTEGER DEFAULT 1")
        
        if 'total_tokens' not in columns:
            print("🔄 Adding total_tokens column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN total_tokens INTEGER DEFAULT 0")
        
        if 'closed_at' not in columns:
            print("🔄 Adding closed_at column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN closed_at TEXT")
            
        if 'custom_instructions' not in columns:
            print("🔄 Adding custom_instructions column to sessions table...")
            cursor.execute("ALTER TABLE sessions ADD COLUMN custom_instructions TEXT DEFAULT ''")
        
        # Interactions table with token tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        
        # Check if tokens_used column exists in interactions table
        cursor.execute("PRAGMA table_info(interactions)")
        interaction_columns = [column[1] for column in cursor.fetchall()]
        
        if 'tokens_used' not in interaction_columns:
            print("🔄 Adding tokens_used column to interactions table...")
            cursor.execute("ALTER TABLE interactions ADD COLUMN tokens_used INTEGER DEFAULT 0")
        
        # Session context table for managing context length
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                context_data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                tokens_count INTEGER DEFAULT 0,
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

def create_new_session(custom_instructions=""):
    """Create a new session with optional custom instructions"""
    global current_session_id
    timestamp = datetime.datetime.now().isoformat()
    session_name = f"Session {timestamp[:19]}"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (created_at, name, is_active, custom_instructions) VALUES (?, ?, ?, ?)",
            (timestamp, session_name, 1, custom_instructions)
        )
        session_id = cursor.lastrowid
        conn.commit()
    
    current_session_id = session_id
    print(f"📝 Created session {session_id}: {session_name}")
    if custom_instructions:
        print(f"🎯 With custom instructions ({len(custom_instructions)} chars)")
    return session_id

def switch_to_session(session_id):
    """Switch to an existing session"""
    global current_session_id
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if session exists
        cursor.execute("SELECT id, name FROM sessions WHERE id = ?", (session_id,))
        session = cursor.fetchone()
        
        if session:
            # Mark previous session as inactive
            if current_session_id:
                cursor.execute(
                    "UPDATE sessions SET is_active = 0 WHERE id = ?",
                    (current_session_id,)
                )
            
            # Mark new session as active
            cursor.execute(
                "UPDATE sessions SET is_active = 1 WHERE id = ?",
                (session_id,)
            )
            
            current_session_id = session_id
            conn.commit()
            print(f"📝 Switched to session {session_id}: {session[1]}")
            return True
        else:
            print(f"❌ Session {session_id} not found")
            return False

def get_current_session():
    """Get current active session"""
    global current_session_id
    
    if current_session_id:
        return current_session_id
    
    # Find the most recent active session
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM sessions WHERE is_active = 1 ORDER BY created_at DESC LIMIT 1"
        )
        result = cursor.fetchone()
        
        if result:
            current_session_id = result[0]
            return current_session_id
        else:
            # Create new session if none exists
            return create_new_session()

def save_session_custom_instructions(session_id, custom_instructions):
    """Save custom instructions for a session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET custom_instructions = ? WHERE id = ?",
            (custom_instructions, session_id)
        )
        conn.commit()
    
    print(f"🎯 Saved custom instructions for session {session_id} ({len(custom_instructions)} chars)")

def get_session_custom_instructions(session_id):
    """Get custom instructions for a session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT custom_instructions FROM sessions WHERE id = ?",
            (session_id,)
        )
        result = cursor.fetchone()
        return result[0] if result and result[0] else ""

def save_interaction(session_id, question, response, tokens_used=0):
    """Save a question-response interaction"""
    timestamp = datetime.datetime.now().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO interactions (session_id, timestamp, question, response, tokens_used) VALUES (?, ?, ?, ?, ?)",
            (session_id, timestamp, question, response, tokens_used)
        )
        
        # Update session token count
        cursor.execute(
            "UPDATE sessions SET total_tokens = total_tokens + ? WHERE id = ?",
            (tokens_used, session_id)
        )
        
        conn.commit()
    
    print(f"💾 Saved interaction for session {session_id} ({tokens_used} tokens)")

def get_session_history(session_id, limit=10):
    """Get recent interactions from a session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT question, response, timestamp, tokens_used FROM interactions WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
        return list(reversed(cursor.fetchall()))  # Return in chronological order

def get_session_context(session_id, max_tokens=4000):
    """Get session context within token limit"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get recent interactions
        cursor.execute(
            "SELECT question, response, tokens_used FROM interactions WHERE session_id = ? ORDER BY timestamp DESC",
            (session_id,)
        )
        interactions = cursor.fetchall()
        
        context_parts = []
        total_tokens = 0
        
        for question, response, tokens_used in interactions:
            # Estimate tokens if not recorded
            if tokens_used == 0:
                tokens_used = len(question.split()) + len(response.split())
            
            if total_tokens + tokens_used > max_tokens:
                break
                
            context_parts.insert(0, f"Q: {question}")
            context_parts.insert(1, f"A: {response[:200]}...")  # Truncate long responses
            total_tokens += tokens_used
        
        return "\n".join(context_parts)

def close_session(session_id):
    """Mark a session as closed"""
    timestamp = datetime.datetime.now().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET closed_at = ?, is_active = 0 WHERE id = ?",
            (timestamp, session_id)
        )
        conn.commit()
    
    print(f"📝 Session {session_id} marked as closed")

def get_all_sessions():
    """Get all sessions ordered by most recent - FIXED to include custom_instructions"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if custom_instructions column exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'custom_instructions' in columns:
            # New query with custom_instructions
            cursor.execute(
                "SELECT id, name, created_at, total_tokens, is_active, custom_instructions FROM sessions ORDER BY created_at DESC"
            )
        else:
            # Fallback for older database schema
            cursor.execute(
                "SELECT id, name, created_at, total_tokens, is_active, '' as custom_instructions FROM sessions ORDER BY created_at DESC"
            )
        
        return cursor.fetchall()

def get_session_info(session_id):
    """Get complete session information including custom instructions - FIXED"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if custom_instructions column exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'custom_instructions' in columns:
            cursor.execute(
                "SELECT id, name, created_at, total_tokens, is_active, custom_instructions FROM sessions WHERE id = ?",
                (session_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1], 
                    'created_at': result[2],
                    'total_tokens': result[3],
                    'is_active': bool(result[4]),
                    'custom_instructions': result[5] or ""
                }
        else:
            # Fallback for older database schema
            cursor.execute(
                "SELECT id, name, created_at, total_tokens, is_active FROM sessions WHERE id = ?",
                (session_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'id': result[0],
                    'name': result[1], 
                    'created_at': result[2],
                    'total_tokens': result[3],
                    'is_active': bool(result[4]),
                    'custom_instructions': ""
                }
        
        return None

def get_session_stats(session_id):
    """Get statistics for a session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get interaction count
        cursor.execute(
            "SELECT COUNT(*) as interaction_count FROM interactions WHERE session_id = ?",
            (session_id,)
        )
        interaction_count = cursor.fetchone()[0]
        
        # Get total tokens
        cursor.execute(
            "SELECT total_tokens FROM sessions WHERE id = ?",
            (session_id,)
        )
        total_tokens = cursor.fetchone()[0] or 0
        
        # Get session duration
        cursor.execute(
            "SELECT created_at, closed_at FROM sessions WHERE id = ?",
            (session_id,)
        )
        session_info = cursor.fetchone()
        
        return {
            'interaction_count': interaction_count,
            'total_tokens': total_tokens,
            'created_at': session_info[0],
            'closed_at': session_info[1]
        }

def cleanup_old_sessions(days_old=30):
    """Clean up old sessions"""
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
    cutoff_str = cutoff_date.isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if is_active column exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' in columns:
            # Use is_active column if it exists
            cursor.execute(
                "SELECT id FROM sessions WHERE created_at < ? AND is_active = 0",
                (cutoff_str,)
            )
        else:
            # Fallback to checking closed_at if is_active doesn't exist
            if 'closed_at' in columns:
                cursor.execute(
                    "SELECT id FROM sessions WHERE created_at < ? AND closed_at IS NOT NULL",
                    (cutoff_str,)
                )
            else:
                # If neither column exists, just clean up very old sessions
                cursor.execute(
                    "SELECT id FROM sessions WHERE created_at < ?",
                    (cutoff_str,)
                )
        
        old_sessions = cursor.fetchall()
        
        if old_sessions:
            session_ids = [s[0] for s in old_sessions]
            
            # Delete interactions
            cursor.execute(
                f"DELETE FROM interactions WHERE session_id IN ({','.join(['?'] * len(session_ids))})",
                session_ids
            )
            
            # Delete sessions
            cursor.execute(
                f"DELETE FROM sessions WHERE id IN ({','.join(['?'] * len(session_ids))})",
                session_ids
            )
            
            conn.commit()
            print(f"🗑️  Cleaned up {len(old_sessions)} old sessions")
        else:
            print("🗑️  No old sessions to clean up")

def get_session_token_count(session_id):
    """Get total token count for a session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT SUM(tokens_used) FROM interactions WHERE session_id = ?",
            (session_id,)
        )
        result = cursor.fetchone()
        return result[0] if result[0] else 0

def save_session_context(session_id, context_data, tokens_count=0):
    """Save session context for efficient retrieval"""
    timestamp = datetime.datetime.now().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO session_contexts (session_id, context_data, created_at, tokens_count) VALUES (?, ?, ?, ?)",
            (session_id, context_data, timestamp, tokens_count)
        )
        conn.commit()

def get_session_context_data(session_id):
    """Get the latest session context data"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT context_data FROM session_contexts WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
            (session_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None

def archive_session(session_id):
    """Archive a session for long-term storage"""
    timestamp = datetime.datetime.now().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Create archive record
        cursor.execute(
            "UPDATE sessions SET closed_at = ?, is_active = 0 WHERE id = ?",
            (timestamp, session_id)
        )
        
        # Compress interaction data
        cursor.execute(
            "SELECT question, response, timestamp FROM interactions WHERE session_id = ?",
            (session_id,)
        )
        interactions = cursor.fetchall()
        
        if interactions:
            # Store compressed summary
            summary = {
                'total_interactions': len(interactions),
                'first_interaction': interactions[0][2],
                'last_interaction': interactions[-1][2],
                'archived_at': timestamp
            }
            
            cursor.execute(
                "INSERT INTO session_contexts (session_id, context_data, created_at, tokens_count) VALUES (?, ?, ?, ?)",
                (session_id, json.dumps(summary), timestamp, 0)
            )
        
        conn.commit()
        print(f"📦 Archived session {session_id}")

def restore_session(session_id):
    """Restore an archived session"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET is_active = 1, closed_at = NULL WHERE id = ?",
            (session_id,)
        )
        conn.commit()
        print(f"📤 Restored session {session_id}")

# New functions for session-based custom instructions
def update_session_name(session_id, new_name):
    """Update session name"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE sessions SET name = ? WHERE id = ?",
            (new_name, session_id)
        )
        conn.commit()
    print(f"📝 Updated session {session_id} name to: {new_name}")

def get_sessions_with_custom_instructions():
    """Get all sessions that have custom instructions"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if custom_instructions column exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'custom_instructions' in columns:
            cursor.execute(
                "SELECT id, name, custom_instructions FROM sessions WHERE custom_instructions != '' AND custom_instructions IS NOT NULL ORDER BY created_at DESC"
            )
            return cursor.fetchall()
        else:
            # Return empty list if column doesn't exist
            return []

def check_session_instructions_locked(session_id):
    """Check if session custom instructions are locked (has interactions)"""
    instructions = get_session_custom_instructions(session_id)
    if not instructions:
        return False
    
    # Check if session has any interactions
    history = get_session_history(session_id, limit=1)
    return len(history) > 0

if __name__ == "__main__":
    print("🗃️  Database Management Module")
    print("Enhanced with custom instructions support")
    
    # Test database functionality
    try:
        initialize_database()
        print("✅ Database initialization test passed")
        
        # Test custom instructions
        test_session = create_new_session("Test custom instructions")
        save_session_custom_instructions(test_session, "Be helpful and concise")
        retrieved = get_session_custom_instructions(test_session)
        print(f"✅ Custom instructions test: '{retrieved}'")
        
        # Test session info
        session_info = get_session_info(test_session)
        print(f"✅ Session info test: {session_info}")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()