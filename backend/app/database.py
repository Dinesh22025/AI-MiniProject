import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os

class Database:
    def __init__(self, db_path="instance/driver_monitor.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_db(self):
        with self.get_connection() as conn:
            # Users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    driver_id TEXT UNIQUE NOT NULL,
                    language TEXT DEFAULT 'en',
                    alert_volume INTEGER DEFAULT 80,
                    theme TEXT DEFAULT 'dark',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Detection events table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS detection_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    event_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    head_tilt REAL DEFAULT 0,
                    gaze_offset REAL DEFAULT 0,
                    faces INTEGER DEFAULT 0,
                    ear REAL DEFAULT 0,
                    mar REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create demo user if not exists
            cursor = conn.execute('SELECT id FROM users WHERE email = ?', ('demo@example.com',))
            if not cursor.fetchone():
                conn.execute('''
                    INSERT INTO users (name, email, password_hash, driver_id)
                    VALUES (?, ?, ?, ?)
                ''', ('Demo User', 'demo@example.com', generate_password_hash('demo123'), 'DEMO001'))
            
            conn.commit()
    
    # User methods
    def create_user(self, name, email, password):
        password_hash = generate_password_hash(password)
        driver_id = f"DRV{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO users (name, email, password_hash, driver_id)
                VALUES (?, ?, ?, ?)
            ''', (name, email, password_hash, driver_id))
            user_id = cursor.lastrowid
            
            # Return user data
            return self.get_user_by_id(user_id)
    
    def get_user_by_email(self, email):
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def verify_password(self, user, password):
        return check_password_hash(user['password_hash'], password)
    
    def update_user_settings(self, user_id, **kwargs):
        if not kwargs:
            return
        
        fields = []
        values = []
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        
        with self.get_connection() as conn:
            conn.execute(query, values)
            conn.commit()
    
    # Detection events methods
    def save_detection_event(self, user_id, event_type, confidence, **meta):
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO detection_events 
                (user_id, event_type, confidence, head_tilt, gaze_offset, faces, ear, mar)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, event_type, confidence,
                meta.get('head_tilt', 0),
                meta.get('gaze_offset', 0),
                meta.get('faces', 0),
                meta.get('ear', 0),
                meta.get('mar', 0)
            ))
            conn.commit()
    
    def get_detection_history(self, user_id, limit=200):
        with self.get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM detection_events 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    'id': row['id'],
                    'eventType': row['event_type'],
                    'confidence': row['confidence'],
                    'meta': {
                        'head_tilt': row['head_tilt'],
                        'gaze_offset': row['gaze_offset'],
                        'faces': row['faces'],
                        'ear': row['ear'],
                        'mar': row['mar'],
                    },
                    'timestamp': row['created_at']
                })
            
            return events
    
    def get_detection_count(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.execute('SELECT COUNT(*) as count FROM detection_events WHERE user_id = ?', (user_id,))
            return cursor.fetchone()['count']
    
    def clear_detection_history(self, user_id):
        with self.get_connection() as conn:
            conn.execute('DELETE FROM detection_events WHERE user_id = ?', (user_id,))
            conn.commit()

# Global database instance
db = Database()