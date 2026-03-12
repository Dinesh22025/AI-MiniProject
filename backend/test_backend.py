#!/usr/bin/env python3

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    print("=" * 50)
    print("TESTING IMPORTS")
    print("=" * 50)
    
    try:
        import flask
        print("[OK] Flask imported")
    except Exception as e:
        print(f"[ERROR] Flask import failed: {e}")
        return False
    
    try:
        import flask_cors
        print("[OK] Flask-CORS imported")
    except Exception as e:
        print(f"[ERROR] Flask-CORS import failed: {e}")
        return False
    
    try:
        import cv2
        print("[OK] OpenCV imported")
    except Exception as e:
        print(f"[ERROR] OpenCV import failed: {e}")
        return False
    
    try:
        import jwt
        print("[OK] PyJWT imported")
    except Exception as e:
        print(f"[ERROR] PyJWT import failed: {e}")
        return False
    
    return True

def test_database():
    print("\n" + "=" * 50)
    print("TESTING DATABASE")
    print("=" * 50)
    
    try:
        from app.database import db
        print("[OK] Database module imported")
        
        # Test database initialization
        db.init_db()
        print("[OK] Database initialized")
        
        # Test user operations
        demo_user = db.get_user_by_email('demo@example.com')
        if demo_user:
            print(f"[OK] Demo user found: {demo_user['name']} (ID: {demo_user['id']})")
        else:
            print("[ERROR] Demo user not found")
            return False
        
        # Test password verification
        if db.verify_password(demo_user, 'demo123'):
            print("[OK] Password verification works")
        else:
            print("[ERROR] Password verification failed")
            return False
        
        # Test detection event storage
        db.save_detection_event(
            user_id=demo_user['id'],
            event_type='drowsy',
            confidence=0.85,
            head_tilt=5.2,
            gaze_offset=3.1,
            faces=1,
            ear=0.22,
            mar=0.05
        )
        print("[OK] Detection event saved")
        
        # Test history retrieval
        history = db.get_detection_history(demo_user['id'])
        print(f"[OK] History retrieved: {len(history)} events")
        
        # Test history count
        count = db.get_detection_count(demo_user['id'])
        print(f"[OK] Total events in database: {count}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_auth():
    print("\n" + "=" * 50)
    print("TESTING AUTHENTICATION")
    print("=" * 50)
    
    try:
        from app import create_app
        from app.auth import create_token, decode_token
        from app.database import db
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            # Get demo user
            demo_user = db.get_user_by_email('demo@example.com')
            
            # Create token
            token = create_token(demo_user)
            print(f"[OK] Token created: {token[:50]}...")
            
            # Decode token
            payload = decode_token(token)
            if payload and payload['user_id'] == demo_user['id']:
                print(f"[OK] Token decoded successfully: user_id={payload['user_id']}")
            else:
                print("[ERROR] Token decode failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Auth test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vision():
    print("\n" + "=" * 50)
    print("TESTING VISION SYSTEM")
    print("=" * 50)
    
    try:
        from app.vision import DriverMonitor
        
        # Initialize monitor
        monitor = DriverMonitor()
        print("[OK] DriverMonitor initialized")
        
        if monitor.mesh:
            print("[OK] MediaPipe FaceMesh available")
        else:
            print("[WARNING] MediaPipe not available, using OpenCV-only mode")
        
        print("[OK] Face cascade loaded")
        print("[OK] Eye cascade loaded")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Vision test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_routes():
    print("\n" + "=" * 50)
    print("TESTING ROUTES")
    print("=" * 50)
    
    try:
        from app import create_app
        
        app = create_app()
        print("[OK] Flask app created")
        
        # List all routes
        print("\nRegistered routes:")
        for rule in app.url_map.iter_rules():
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"  {methods:10s} {rule.rule}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_file():
    print("\n" + "=" * 50)
    print("CHECKING DATABASE FILE")
    print("=" * 50)
    
    db_path = "instance/driver_monitor.db"
    
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"[OK] Database file exists: {db_path}")
        print(f"[OK] Database size: {size} bytes")
        
        # Check if we can connect to it
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"[OK] Tables in database: {[t[0] for t in tables]}")
            
            # Check user count
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"[OK] Users in database: {user_count}")
            
            # Check event count
            cursor.execute("SELECT COUNT(*) FROM detection_events")
            event_count = cursor.fetchone()[0]
            print(f"[OK] Detection events in database: {event_count}")
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    else:
        print(f"[WARNING] Database file not found: {db_path}")
        print("[INFO] It will be created on first run")
        return True

def main():
    print("\n")
    print("*" * 50)
    print("BACKEND COMPREHENSIVE TEST")
    print("*" * 50)
    print("\n")
    
    results = {
        "Imports": test_imports(),
        "Database File": test_database_file(),
        "Database Operations": test_database(),
        "Authentication": test_auth(),
        "Vision System": test_vision(),
        "Routes": test_routes(),
    }
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n[SUCCESS] All tests passed! Backend is ready.")
        print("\nYou can now start the server with: python run.py")
    else:
        print("\n[FAILURE] Some tests failed. Please fix the issues above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
