#!/usr/bin/env python3
"""
Migration Script: Convert existing JSON data to SQLite database
This script migrates your existing darknet crawler data to the new SQLite database
"""

import os
import json
import sys
from datetime import datetime
from database.models import DatabaseManager, Alert, CrawledPage

def migrate_existing_data():
    """Migrate existing JSON files to SQLite database"""
    print("🔄 Starting migration from JSON to SQLite...")
    print("=" * 50)
    
    # Initialize database manager
    db = DatabaseManager("darknet_intelligence.db")
    
    # Define file paths
    json_files = {
        "alerts": "alert_log.json",
        "visited": "visited_links.json",
        "non_http": "non_http_links.json",
        "output": "output.json"
    }
    
    # Check which files exist
    existing_files = {}
    for file_type, file_path in json_files.items():
        if os.path.exists(file_path):
            existing_files[file_type] = file_path
            print(f"✅ Found {file_type} file: {file_path}")
        else:
            print(f"⚠️  {file_type} file not found: {file_path}")
    
    if not existing_files:
        print("❌ No existing JSON files found to migrate")
        return False
    
    print("\\n🔄 Starting migration process...")
    
    # Migrate alerts
    if "alerts" in existing_files:
        print("\\n📊 Migrating alerts...")
        alert_count = 0
        
        try:
            with open(existing_files["alerts"], "r") as f:
                for line_no, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        alert_data = json.loads(line)
                        
                        # Create Alert object
                        alert = Alert(
                            timestamp=alert_data.get("timestamp", datetime.now().isoformat()),
                            url=alert_data.get("url", ""),
                            title=alert_data.get("title", "No Title"),
                            keywords_found=alert_data.get("keywords_found", []),
                            content_hash=str(hash(alert_data.get("url", "") + str(alert_data.get("keywords_found", [])))),
                            threat_level=db._determine_threat_level(alert_data.get("keywords_found", [])),
                            source_type="web",
                            processed=False
                        )
                        
                        # Insert into database
                        result = db.insert_alert(alert)
                        if result > 0:
                            alert_count += 1
                            if alert_count % 100 == 0:
                                print(f"   📈 Migrated {alert_count} alerts...")
                        
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️  Skipping malformed JSON on line {line_no}: {e}")
                        continue
                    except Exception as e:
                        print(f"   ⚠️  Error processing alert on line {line_no}: {e}")
                        continue
        
        except Exception as e:
            print(f"   ❌ Error reading alerts file: {e}")
        
        print(f"   ✅ Migrated {alert_count} alerts")
    
    # Migrate visited links
    if "visited" in existing_files:
        print("\\n🌐 Migrating visited links...")
        page_count = 0
        
        try:
            with open(existing_files["visited"], "r") as f:
                visited_links = json.load(f)
                
                for url in visited_links:
                    try:
                        page = CrawledPage(
                            url=url,
                            title="",
                            content_hash=str(hash(url)),
                            timestamp=datetime.now().isoformat(),
                            response_code=200,
                            processing_time=0.0,
                            page_size=0,
                            links_found=0
                        )
                        
                        result = db.insert_crawled_page(page)
                        if result > 0:
                            page_count += 1
                            if page_count % 100 == 0:
                                print(f"   📈 Migrated {page_count} pages...")
                    
                    except Exception as e:
                        print(f"   ⚠️  Error processing URL {url}: {e}")
                        continue
        
        except Exception as e:
            print(f"   ❌ Error reading visited links file: {e}")
        
        print(f"   ✅ Migrated {page_count} visited pages")
    
    # Migrate non-HTTP links
    if "non_http" in existing_files:
        print("\\n📧 Migrating non-HTTP links...")
        non_http_count = 0
        
        try:
            with open(existing_files["non_http"], "r") as f:
                non_http_links = json.load(f)
                
                with db.get_cursor() as cursor:
                    for link in non_http_links:
                        try:
                            cursor.execute("""
                                INSERT INTO non_http_links (source_url, link_type, link_value, discovered_at)
                                VALUES (?, ?, ?, ?)
                            """, (
                                link.get("source", ""),
                                link.get("type", ""),
                                link.get("value", ""),
                                datetime.now().isoformat()
                            ))
                            non_http_count += 1
                        
                        except Exception as e:
                            print(f"   ⚠️  Error processing non-HTTP link: {e}")
                            continue
        
        except Exception as e:
            print(f"   ❌ Error reading non-HTTP links file: {e}")
        
        print(f"   ✅ Migrated {non_http_count} non-HTTP links")
    
    # Create backup of original files
    print("\\n💾 Creating backup of original files...")
    backup_dir = f"json_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    for file_type, file_path in existing_files.items():
        try:
            import shutil
            backup_path = os.path.join(backup_dir, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            print(f"   ✅ Backed up {file_path} to {backup_path}")
        except Exception as e:
            print(f"   ⚠️  Error backing up {file_path}: {e}")
    
    # Generate migration report
    print("\\n📊 Migration Summary:")
    print("=" * 30)
    
    stats = db.get_threat_statistics()
    print(f"📈 Total alerts migrated: {stats.get('total_alerts', 0)}")
    print(f"🌐 Total pages migrated: {stats.get('total_pages', 0)}")
    print(f"📊 Alerts by threat level: {stats.get('alerts_by_level', {})}")
    print(f"💾 Backup created in: {backup_dir}")
    
    print("\\n✅ Migration completed successfully!")
    print("🎉 Your darknet crawler is now using SQLite for enhanced performance!")
    
    return True

def verify_migration():
    """Verify the migration was successful"""
    print("\\n🔍 Verifying migration...")
    
    db = DatabaseManager("darknet_intelligence.db")
    
    # Check database exists and has data
    if not os.path.exists("darknet_intelligence.db"):
        print("❌ Database file not found")
        return False
    
    stats = db.get_threat_statistics()
    alerts = db.get_alerts(limit=5)
    pages = db.get_crawled_pages(limit=5)
    
    print(f"✅ Database contains {stats.get('total_alerts', 0)} alerts")
    print(f"✅ Database contains {stats.get('total_pages', 0)} pages")
    
    if alerts:
        print("✅ Sample alerts found:")
        for alert in alerts[:3]:
            print(f"   - {alert.get('threat_level', 'UNKNOWN')}: {alert.get('url', 'No URL')}")
    
    return True

if __name__ == "__main__":
    print("🚀 Darknet Crawler Migration Tool")
    print("=" * 50)
    
    # Check if database already exists
    if os.path.exists("darknet_intelligence.db"):
        print("⚠️  SQLite database already exists. Removing...")
        os.remove("darknet_intelligence.db")
    
    # Run migration
    success = migrate_existing_data()
    
    if success:
        verify_migration()
        print("\\n🎯 Next steps:")
        print("1. Test the new crawler with: python3 test_phase1.py")
        print("2. Run the dashboard with: streamlit run dashboard.py")
        print("3. Start crawling with the enhanced SQLite backend!")
    else:
        print("❌ Migration failed. Please check the errors above.")
        sys.exit(1)
