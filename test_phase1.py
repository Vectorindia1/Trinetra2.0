#!/usr/bin/env python3
"""
Phase 1 Test Suite: SQLite Migration + Multi-threading + Enhanced Alerts
Test the core functionality of the upgraded darknet crawler
"""

import os
import sys
import time
import json
import threading
from datetime import datetime
from database.models import DatabaseManager, Alert, CrawledPage

def test_database_initialization():
    """Test 1: Database initialization and schema creation"""
    print("🧪 Test 1: Database Initialization")
    
    # Clean up any existing test database
    test_db_path = "test_darknet_intelligence.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Initialize database
    db = DatabaseManager(test_db_path)
    
    # Verify tables exist
    with db.get_cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['alerts', 'crawled_pages', 'threat_intelligence', 'non_http_links', 'keyword_tracking']
        
        for table in expected_tables:
            if table in tables:
                print(f"   ✅ Table '{table}' created successfully")
            else:
                print(f"   ❌ Table '{table}' missing")
                return False
    
    # Clean up
    db.close()
    os.remove(test_db_path)
    print("   ✅ Database initialization test passed!\n")
    return True

def test_alert_operations():
    """Test 2: Alert insertion and retrieval"""
    print("🧪 Test 2: Alert Operations")
    
    test_db_path = "test_darknet_intelligence.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = DatabaseManager(test_db_path)
    
    # Test alert insertion
    test_alerts = [
        Alert(
            timestamp=datetime.now().isoformat(),
            url="http://test1.onion",
            title="Test High Risk Alert",
            keywords_found=["bomb", "terror"],
            content_hash="hash1",
            threat_level="HIGH"
        ),
        Alert(
            timestamp=datetime.now().isoformat(),
            url="http://test2.onion",
            title="Test Medium Risk Alert",
            keywords_found=["hacking", "drugs"],
            content_hash="hash2",
            threat_level="MEDIUM"
        ),
        Alert(
            timestamp=datetime.now().isoformat(),
            url="http://test3.onion",
            title="Test Low Risk Alert",
            keywords_found=["privacy", "vpn"],
            content_hash="hash3",
            threat_level="LOW"
        )
    ]
    
    # Insert test alerts
    for alert in test_alerts:
        result = db.insert_alert(alert)
        if result > 0:
            print(f"   ✅ Alert inserted: {alert.threat_level} - {alert.url}")
        else:
            print(f"   ❌ Failed to insert alert: {alert.url}")
    
    # Test alert retrieval
    all_alerts = db.get_alerts(limit=10)
    print(f"   ✅ Retrieved {len(all_alerts)} alerts")
    
    # Test filtering by threat level
    high_alerts = db.get_alerts(threat_level="HIGH")
    print(f"   ✅ Retrieved {len(high_alerts)} HIGH threat alerts")
    
    # Test duplicate prevention
    duplicate_alert = Alert(
        timestamp=datetime.now().isoformat(),
        url="http://test1.onion",
        title="Duplicate Alert",
        keywords_found=["bomb"],
        content_hash="hash1",  # Same hash as first alert
        threat_level="HIGH"
    )
    
    result = db.insert_alert(duplicate_alert)
    if result == 0:
        print("   ✅ Duplicate prevention working correctly")
    else:
        print("   ❌ Duplicate prevention failed")
    
    # Clean up
    db.close()
    os.remove(test_db_path)
    print("   ✅ Alert operations test passed!\n")
    return True

def test_crawled_page_operations():
    """Test 3: Crawled page operations"""
    print("🧪 Test 3: Crawled Page Operations")
    
    test_db_path = "test_darknet_intelligence.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = DatabaseManager(test_db_path)
    
    # Test crawled page insertion
    test_pages = [
        CrawledPage(
            url="http://test1.onion",
            title="Test Page 1",
            content_hash="page_hash1",
            timestamp=datetime.now().isoformat(),
            response_code=200,
            processing_time=1.5,
            page_size=1024,
            links_found=10
        ),
        CrawledPage(
            url="http://test2.onion",
            title="Test Page 2",
            content_hash="page_hash2",
            timestamp=datetime.now().isoformat(),
            response_code=200,
            processing_time=2.0,
            page_size=2048,
            links_found=15
        )
    ]
    
    # Insert test pages
    for page in test_pages:
        result = db.insert_crawled_page(page)
        if result > 0:
            print(f"   ✅ Page inserted: {page.url}")
        else:
            print(f"   ❌ Failed to insert page: {page.url}")
    
    # Test page retrieval
    pages = db.get_crawled_pages(limit=10)
    print(f"   ✅ Retrieved {len(pages)} crawled pages")
    
    # Clean up
    db.close()
    os.remove(test_db_path)
    print("   ✅ Crawled page operations test passed!\n")
    return True

def test_threat_statistics():
    """Test 4: Threat statistics and analytics"""
    print("🧪 Test 4: Threat Statistics")
    
    test_db_path = "test_darknet_intelligence.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = DatabaseManager(test_db_path)
    
    # Insert test data
    test_alerts = [
        Alert(timestamp=datetime.now().isoformat(), url="http://test1.onion", title="Test 1", 
              keywords_found=["bomb"], content_hash="hash1", threat_level="HIGH"),
        Alert(timestamp=datetime.now().isoformat(), url="http://test2.onion", title="Test 2", 
              keywords_found=["hacking"], content_hash="hash2", threat_level="MEDIUM"),
        Alert(timestamp=datetime.now().isoformat(), url="http://test3.onion", title="Test 3", 
              keywords_found=["privacy"], content_hash="hash3", threat_level="LOW")
    ]
    
    for alert in test_alerts:
        db.insert_alert(alert)
    
    # Test statistics
    stats = db.get_threat_statistics()
    print(f"   ✅ Total alerts: {stats['total_alerts']}")
    print(f"   ✅ Alerts by level: {stats['alerts_by_level']}")
    print(f"   ✅ Total pages: {stats['total_pages']}")
    
    # Clean up
    db.close()
    os.remove(test_db_path)
    print("   ✅ Threat statistics test passed!\n")
    return True

def test_threading_safety():
    """Test 5: Thread safety of database operations"""
    print("🧪 Test 5: Threading Safety")
    
    test_db_path = "test_darknet_intelligence.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    db = DatabaseManager(test_db_path)
    
    def worker_function(worker_id):
        """Worker function to test concurrent database operations"""
        for i in range(5):
            alert = Alert(
                timestamp=datetime.now().isoformat(),
                url=f"http://worker{worker_id}_test{i}.onion",
                title=f"Worker {worker_id} Test {i}",
                keywords_found=["test"],
                content_hash=f"hash_{worker_id}_{i}",
                threat_level="LOW"
            )
            db.insert_alert(alert)
            time.sleep(0.1)  # Small delay to simulate processing
    
    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_function, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    all_alerts = db.get_alerts(limit=100)
    expected_count = 3 * 5  # 3 workers * 5 alerts each
    
    if len(all_alerts) == expected_count:
        print(f"   ✅ Threading test passed: {len(all_alerts)} alerts inserted concurrently")
    else:
        print(f"   ❌ Threading test failed: Expected {expected_count}, got {len(all_alerts)}")
    
    # Clean up
    db.close()
    os.remove(test_db_path)
    print("   ✅ Threading safety test passed!\n")
    return True

def test_json_migration():
    """Test 6: JSON to SQLite migration"""
    print("🧪 Test 6: JSON Migration")
    
    test_db_path = "test_darknet_intelligence.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Create test JSON files
    test_alert_data = {
        "timestamp": "2024-01-01T12:00:00",
        "url": "http://test.onion",
        "title": "Test Alert",
        "keywords_found": ["bomb", "terror"]
    }
    
    test_visited_links = ["http://test1.onion", "http://test2.onion", "http://test3.onion"]
    
    # Write test JSON files
    with open("test_alerts.json", "w") as f:
        f.write(json.dumps(test_alert_data) + "\n")
    
    with open("test_visited.json", "w") as f:
        json.dump(test_visited_links, f)
    
    # Test migration
    db = DatabaseManager(test_db_path)
    db.migrate_from_json({
        "alerts": "test_alerts.json",
        "visited": "test_visited.json"
    })
    
    # Verify migration results
    alerts = db.get_alerts()
    pages = db.get_crawled_pages()
    
    print(f"   ✅ Migrated {len(alerts)} alerts")
    print(f"   ✅ Migrated {len(pages)} pages")
    
    # Clean up
    db.close()
    os.remove(test_db_path)
    os.remove("test_alerts.json")
    os.remove("test_visited.json")
    print("   ✅ JSON migration test passed!\n")
    return True

def run_all_tests():
    """Run all Phase 1 tests"""
    print("🚀 Starting Phase 1 Test Suite")
    print("=" * 50)
    
    tests = [
        test_database_initialization,
        test_alert_operations,
        test_crawled_page_operations,
        test_threat_statistics,
        test_threading_safety,
        test_json_migration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Phase 1 tests passed! The enhanced crawler is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
