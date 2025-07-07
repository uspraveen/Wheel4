#!/usr/bin/env python3
"""
Wheel4 - Database Reset Utility
Manual database reset and cleanup tools
"""

import os
import sys
import sqlite3
import datetime
from pathlib import Path

# Add the current directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    DB_FILE, get_connection, initialize_database, 
    cleanup_old_sessions, get_all_sessions, get_session_stats
)

def print_banner():
    """Print application banner"""
    print("=" * 60)
    print("🧠 Wheel4 AI Brain - Database Reset Utility")
    print("=" * 60)
    print()

def backup_database():
    """Create backup of current database"""
    if not os.path.exists(DB_FILE):
        print("❌ No database file found to backup")
        return None
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"ai_brain_backup_{timestamp}.db"
    
    try:
        # Copy database file
        import shutil
        shutil.copy2(DB_FILE, backup_file)
        print(f"✅ Database backed up to: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def show_database_stats():
    """Show current database statistics"""
    if not os.path.exists(DB_FILE):
        print("❌ No database file found")
        return
    
    try:
        sessions = get_all_sessions()
        print(f"📊 Database Statistics:")
        print(f"   • Total sessions: {len(sessions)}")
        
        if sessions:
            # Get stats for recent sessions
            active_sessions = [s for s in sessions if s[4] == 1]  # is_active = 1
            closed_sessions = [s for s in sessions if s[4] == 0]  # is_active = 0
            
            print(f"   • Active sessions: {len(active_sessions)}")
            print(f"   • Closed sessions: {len(closed_sessions)}")
            
            # Show recent sessions
            print(f"\n📝 Recent Sessions:")
            for i, (session_id, name, created_at, total_tokens, is_active) in enumerate(sessions[:5]):
                status = "Active" if is_active else "Closed"
                print(f"   • Session {session_id}: {status} ({total_tokens} tokens)")
        
        # Get database file size
        db_size = os.path.getsize(DB_FILE) / 1024  # KB
        print(f"   • Database size: {db_size:.1f} KB")
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")

def clean_old_sessions():
    """Clean up old sessions interactively"""
    print("🧹 Session Cleanup Options:")
    print("1. Clean sessions older than 30 days")
    print("2. Clean sessions older than 7 days")
    print("3. Clean sessions older than 1 day")
    print("4. Clean all closed sessions")
    print("5. Cancel")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    try:
        if choice == "1":
            cleanup_old_sessions(days_old=30)
        elif choice == "2":
            cleanup_old_sessions(days_old=7)
        elif choice == "3":
            cleanup_old_sessions(days_old=1)
        elif choice == "4":
            # Clean all closed sessions
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM sessions WHERE is_active = 0")
                closed_sessions = cursor.fetchall()
                
                if closed_sessions:
                    session_ids = [s[0] for s in closed_sessions]
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
                    print(f"✅ Cleaned up {len(closed_sessions)} closed sessions")
                else:
                    print("ℹ️  No closed sessions to clean up")
        elif choice == "5":
            print("❌ Cleanup cancelled")
        else:
            print("❌ Invalid choice")
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

def reset_database():
    """Complete database reset"""
    if os.path.exists(DB_FILE):
        print("⚠️  This will completely reset the database!")
        print("   • All sessions will be lost")
        print("   • All conversation history will be lost")
        print("   • API keys will be preserved")
        
        confirm = input("\nAre you sure? Type 'RESET' to confirm: ").strip()
        
        if confirm == "RESET":
            # Backup first
            backup_file = backup_database()
            if backup_file:
                print(f"📦 Backup created: {backup_file}")
            
            try:
                # Get API key before reset
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT api_key FROM api_keys ORDER BY updated_at DESC LIMIT 1")
                    api_key_result = cursor.fetchone()
                    api_key = api_key_result[0] if api_key_result else None
                
                # Delete database file
                os.remove(DB_FILE)
                print("🗑️  Database file deleted")
                
                # Recreate database
                initialize_database()
                print("🔄 Database recreated")
                
                # Restore API key if it existed
                if api_key:
                    from database import save_api_key
                    save_api_key(api_key)
                    print("🔑 API key restored")
                
                print("✅ Database reset complete!")
                
            except Exception as e:
                print(f"❌ Reset failed: {e}")
        else:
            print("❌ Reset cancelled")
    else:
        print("ℹ️  No database file found to reset")

def reset_api_key():
    """Reset API key only"""
    confirm = input("⚠️  Reset API key? You'll need to re-enter it. (y/N): ").strip().lower()
    
    if confirm == 'y':
        try:
            from database import save_api_key
            save_api_key("")
            print("✅ API key reset")
        except Exception as e:
            print(f"❌ API key reset failed: {e}")
    else:
        print("❌ API key reset cancelled")

def export_sessions():
    """Export sessions to JSON"""
    if not os.path.exists(DB_FILE):
        print("❌ No database file found")
        return
    
    try:
        import json
        
        sessions = get_all_sessions()
        export_data = {
            "export_date": datetime.datetime.now().isoformat(),
            "total_sessions": len(sessions),
            "sessions": []
        }
        
        for session_id, name, created_at, total_tokens, is_active in sessions:
            # Get interactions for this session
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT question, response, timestamp FROM interactions WHERE session_id = ? ORDER BY timestamp",
                    (session_id,)
                )
                interactions = cursor.fetchall()
            
            session_data = {
                "id": session_id,
                "name": name,
                "created_at": created_at,
                "total_tokens": total_tokens,
                "is_active": bool(is_active),
                "interactions": [
                    {
                        "question": q,
                        "response": r,
                        "timestamp": t
                    }
                    for q, r, t in interactions
                ]
            }
            export_data["sessions"].append(session_data)
        
        # Save export file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = f"sessions_export_{timestamp}.json"
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sessions exported to: {export_file}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")

def main_menu():
    """Main menu interface"""
    while True:
        print("\n🔧 Database Management Options:")
        print("1. Show database statistics")
        print("2. Clean old sessions")
        print("3. Export sessions to JSON")
        print("4. Reset API key")
        print("5. Complete database reset")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            show_database_stats()
        elif choice == "2":
            clean_old_sessions()
        elif choice == "3":
            export_sessions()
        elif choice == "4":
            reset_api_key()
        elif choice == "5":
            reset_database()
        elif choice == "6":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

def main():
    """Main function"""
    print_banner()
    
    # Check if database exists
    if os.path.exists(DB_FILE):
        print(f"📁 Database found: {DB_FILE}")
        show_database_stats()
    else:
        print("📁 No database file found")
        print("   The database will be created when you first run the application")
    
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()