#!/usr/bin/env python3
"""
Database cleanup script for Driver AI Co-Pilot
Removes duplicate detection events and optimizes the database
"""
import sqlite3
import os
from datetime import datetime, timedelta

class DatabaseCleaner:
    def __init__(self, db_path="instance/driver_monitor.db"):
        self.db_path = db_path
        
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def backup_database(self):
        """Create a backup before cleaning"""
        if not os.path.exists(self.db_path):
            print("❌ Database file not found!")
            return False
            
        backup_path = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Database backed up to: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def analyze_duplicates(self):
        """Analyze duplicate detection events"""
        with self.get_connection() as conn:
            # Check for exact duplicates (same user, event_type, confidence, timestamp within 1 second)
            cursor = conn.execute('''
                SELECT user_id, event_type, confidence, 
                       datetime(created_at) as created_time,
                       COUNT(*) as count
                FROM detection_events 
                GROUP BY user_id, event_type, confidence, 
                         strftime('%Y-%m-%d %H:%M:%S', created_at)
                HAVING COUNT(*) > 1
                ORDER BY count DESC
            ''')
            
            duplicates = cursor.fetchall()
            total_duplicates = sum(row['count'] - 1 for row in duplicates)
            
            print(f"📊 Duplicate Analysis:")
            print(f"   Duplicate groups: {len(duplicates)}")
            print(f"   Total duplicate records: {total_duplicates}")
            
            if duplicates:
                print("\n🔍 Top duplicate groups:")
                for i, row in enumerate(duplicates[:5]):
                    print(f"   {i+1}. User {row['user_id']}, {row['event_type']}, "
                          f"confidence {row['confidence']:.2f} - {row['count']} records")
            
            return total_duplicates > 0
    
    def remove_duplicates(self):
        """Remove duplicate detection events"""
        with self.get_connection() as conn:
            # Keep only the first occurrence of each duplicate group
            cursor = conn.execute('''
                DELETE FROM detection_events 
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM detection_events
                    GROUP BY user_id, event_type, confidence, 
                             strftime('%Y-%m-%d %H:%M:%S', created_at)
                )
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"🗑️  Removed {deleted_count} duplicate records")
            return deleted_count
    
    def remove_old_events(self, days=30):
        """Remove detection events older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                DELETE FROM detection_events 
                WHERE created_at < ?
            ''', (cutoff_date.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"🗑️  Removed {deleted_count} events older than {days} days")
            return deleted_count
    
    def optimize_database(self):
        """Optimize database performance"""
        with self.get_connection() as conn:
            # Create indexes for better performance
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_detection_events_user_id 
                ON detection_events(user_id)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_detection_events_created_at 
                ON detection_events(created_at)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_detection_events_event_type 
                ON detection_events(event_type)
            ''')
            
            # Vacuum to reclaim space
            conn.execute('VACUUM')
            conn.commit()
            
            print("✅ Database optimized with indexes and vacuum")
    
    def get_statistics(self):
        """Get database statistics"""
        with self.get_connection() as conn:
            # Total events
            cursor = conn.execute('SELECT COUNT(*) as total FROM detection_events')
            total_events = cursor.fetchone()['total']
            
            # Events by type
            cursor = conn.execute('''
                SELECT event_type, COUNT(*) as count 
                FROM detection_events 
                GROUP BY event_type 
                ORDER BY count DESC
            ''')
            events_by_type = cursor.fetchall()
            
            # Events by user
            cursor = conn.execute('''
                SELECT u.name, u.email, COUNT(de.id) as event_count
                FROM users u
                LEFT JOIN detection_events de ON u.id = de.user_id
                GROUP BY u.id, u.name, u.email
                ORDER BY event_count DESC
            ''')
            events_by_user = cursor.fetchall()
            
            # Recent events (last 24 hours)
            cursor = conn.execute('''
                SELECT COUNT(*) as recent_count 
                FROM detection_events 
                WHERE created_at > datetime('now', '-1 day')
            ''')
            recent_events = cursor.fetchone()['recent_count']
            
            print(f"\n📈 Database Statistics:")
            print(f"   Total detection events: {total_events}")
            print(f"   Recent events (24h): {recent_events}")
            
            print(f"\n📊 Events by type:")
            for row in events_by_type:
                print(f"   {row['event_type']}: {row['count']}")
            
            print(f"\n👥 Events by user:")
            for row in events_by_user:
                print(f"   {row['name']} ({row['email']}): {row['event_count']}")
    
    def clean_database(self, remove_old_days=None):
        """Main cleanup function"""
        print("🧹 Starting database cleanup...")
        print("=" * 50)
        
        if not os.path.exists(self.db_path):
            print("❌ Database file not found!")
            return False
        
        # Backup first
        if not self.backup_database():
            return False
        
        # Show initial statistics
        print("\n📊 Initial Statistics:")
        self.get_statistics()
        
        # Analyze duplicates
        print("\n🔍 Analyzing duplicates...")
        has_duplicates = self.analyze_duplicates()
        
        # Remove duplicates
        if has_duplicates:
            print("\n🗑️  Removing duplicates...")
            self.remove_duplicates()
        else:
            print("✅ No duplicates found")
        
        # Remove old events if specified
        if remove_old_days:
            print(f"\n🗑️  Removing events older than {remove_old_days} days...")
            self.remove_old_events(remove_old_days)
        
        # Optimize database
        print("\n⚡ Optimizing database...")
        self.optimize_database()
        
        # Show final statistics
        print("\n📊 Final Statistics:")
        self.get_statistics()
        
        print("\n✅ Database cleanup completed!")
        return True

def main():
    """Main function"""
    import sys
    
    cleaner = DatabaseCleaner()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove-old":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            cleaner.clean_database(remove_old_days=days)
        elif sys.argv[1] == "--stats":
            cleaner.get_statistics()
        elif sys.argv[1] == "--duplicates":
            cleaner.analyze_duplicates()
        else:
            print("Usage:")
            print("  python cleanup_database.py                    # Clean duplicates only")
            print("  python cleanup_database.py --remove-old [days] # Clean duplicates and old events")
            print("  python cleanup_database.py --stats            # Show statistics only")
            print("  python cleanup_database.py --duplicates       # Analyze duplicates only")
    else:
        cleaner.clean_database()

if __name__ == "__main__":
    main()