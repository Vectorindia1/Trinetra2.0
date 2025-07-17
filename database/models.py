"""
Database Models and Schema for Enhanced Darknet Crawler
Phase 1: SQLite Migration with Performance Optimizations
"""

import sqlite3
import json
import os
import threading
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Alert:
    """Alert data model"""
    id: Optional[int] = None
    timestamp: str = ""
    url: str = ""
    title: str = ""
    keywords_found: List[str] = None
    content_hash: str = ""
    threat_level: str = "LOW"
    source_type: str = "web"
    processed: bool = False
    
    def __post_init__(self):
        if self.keywords_found is None:
            self.keywords_found = []

@dataclass
class CrawledPage:
    """Crawled page data model"""
    id: Optional[int] = None
    url: str = ""
    title: str = ""
    content_hash: str = ""
    timestamp: str = ""
    response_code: int = 200
    processing_time: float = 0.0
    page_size: int = 0
    links_found: int = 0

@dataclass
class ThreatIntelligence:
    """Threat intelligence data model"""
    id: Optional[int] = None
    keyword: str = ""
    threat_level: str = "LOW"
    category: str = ""
    confidence_score: float = 0.0
    last_seen: str = ""
    frequency: int = 0

class DatabaseManager:
    """Thread-safe SQLite database manager with connection pooling"""
    
    def __init__(self, db_path: str = "darknet_intelligence.db"):
        self.db_path = db_path
        self.local = threading.local()
        self.lock = threading.Lock()
        self.initialize_database()
        
    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self.local.connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent performance
            self.local.connection.execute("PRAGMA journal_mode=WAL")
            self.local.connection.execute("PRAGMA synchronous=NORMAL")
            self.local.connection.execute("PRAGMA cache_size=10000")
            self.local.connection.execute("PRAGMA temp_store=MEMORY")
        return self.local.connection
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database operations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        else:
            conn.commit()
        finally:
            cursor.close()
    
    def initialize_database(self):
        """Initialize database schema with optimized indexes"""
        with self.lock:
            with self.get_cursor() as cursor:
                # Alerts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        url TEXT NOT NULL,
                        title TEXT,
                        keywords_found TEXT NOT NULL,
                        content_hash TEXT UNIQUE,
                        threat_level TEXT DEFAULT 'LOW',
                        source_type TEXT DEFAULT 'web',
                        processed BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Crawled pages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawled_pages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT UNIQUE NOT NULL,
                        title TEXT,
                        content_hash TEXT UNIQUE,
                        timestamp TEXT NOT NULL,
                        response_code INTEGER DEFAULT 200,
                        processing_time REAL DEFAULT 0.0,
                        page_size INTEGER DEFAULT 0,
                        links_found INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Threat intelligence table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS threat_intelligence (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT NOT NULL,
                        threat_level TEXT DEFAULT 'LOW',
                        category TEXT,
                        confidence_score REAL DEFAULT 0.0,
                        last_seen TEXT,
                        frequency INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Non-HTTP links table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS non_http_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_url TEXT NOT NULL,
                        link_type TEXT NOT NULL,
                        link_value TEXT NOT NULL,
                        discovered_at TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Keywords tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS keyword_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT NOT NULL,
                        category TEXT,
                        priority INTEGER DEFAULT 1,
                        active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create optimized indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_alerts_url ON alerts(url)",
                    "CREATE INDEX IF NOT EXISTS idx_alerts_threat_level ON alerts(threat_level)",
                    "CREATE INDEX IF NOT EXISTS idx_alerts_processed ON alerts(processed)",
                    "CREATE INDEX IF NOT EXISTS idx_crawled_url ON crawled_pages(url)",
                    "CREATE INDEX IF NOT EXISTS idx_crawled_timestamp ON crawled_pages(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_threat_keyword ON threat_intelligence(keyword)",
                    "CREATE INDEX IF NOT EXISTS idx_threat_level ON threat_intelligence(threat_level)",
                    "CREATE INDEX IF NOT EXISTS idx_nonhttp_type ON non_http_links(link_type)",
                    "CREATE INDEX IF NOT EXISTS idx_keyword_active ON keyword_tracking(active)",
                ]
                
                for index in indexes:
                    cursor.execute(index)
                
                logger.info("✅ Database initialized successfully")
    
    def insert_alert(self, alert: Alert) -> int:
        """Insert alert with duplicate prevention"""
        with self.get_cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO alerts 
                    (timestamp, url, title, keywords_found, content_hash, threat_level, source_type, processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.timestamp,
                    alert.url,
                    alert.title,
                    json.dumps(alert.keywords_found),
                    alert.content_hash,
                    alert.threat_level,
                    alert.source_type,
                    alert.processed
                ))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                logger.warning(f"Duplicate alert ignored: {alert.url}")
                return 0
    
    def insert_crawled_page(self, page: CrawledPage) -> int:
        """Insert crawled page with duplicate prevention"""
        with self.get_cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO crawled_pages 
                    (url, title, content_hash, timestamp, response_code, processing_time, page_size, links_found)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    page.url,
                    page.title,
                    page.content_hash,
                    page.timestamp,
                    page.response_code,
                    page.processing_time,
                    page.page_size,
                    page.links_found
                ))
                return cursor.lastrowid
            except sqlite3.Error as e:
                logger.error(f"Error inserting crawled page: {e}")
                return 0
    
    def update_threat_intelligence(self, keyword: str, threat_level: str, category: str = None):
        """Update or insert threat intelligence data"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO threat_intelligence (keyword, threat_level, category, last_seen, frequency)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(keyword) DO UPDATE SET
                    threat_level = excluded.threat_level,
                    category = excluded.category,
                    last_seen = excluded.last_seen,
                    frequency = frequency + 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (keyword, threat_level, category, datetime.now().isoformat()))
    
    def get_alerts(self, limit: int = 100, threat_level: str = None, processed: bool = None) -> List[Dict]:
        """Get alerts with filtering options"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            
            if threat_level:
                query += " AND threat_level = ?"
                params.append(threat_level)
            
            if processed is not None:
                query += " AND processed = ?"
                params.append(processed)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_crawled_pages(self, limit: int = 100) -> List[Dict]:
        """Get crawled pages"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM crawled_pages 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_threat_statistics(self) -> Dict:
        """Get comprehensive threat statistics"""
        with self.get_cursor() as cursor:
            stats = {}
            
            # Alert statistics
            cursor.execute("SELECT COUNT(*) FROM alerts")
            stats['total_alerts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT threat_level, COUNT(*) FROM alerts GROUP BY threat_level")
            stats['alerts_by_level'] = dict(cursor.fetchall())
            
            # Crawled pages statistics
            cursor.execute("SELECT COUNT(*) FROM crawled_pages")
            stats['total_pages'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(processing_time) FROM crawled_pages")
            stats['avg_processing_time'] = cursor.fetchone()[0] or 0.0
            
            # Top keywords
            cursor.execute("""
                SELECT keyword, frequency 
                FROM threat_intelligence 
                ORDER BY frequency DESC 
                LIMIT 10
            """)
            stats['top_keywords'] = dict(cursor.fetchall())
            
            return stats
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data to maintain performance"""
        with self.get_cursor() as cursor:
            cutoff_date = datetime.now().replace(days=days * -1).isoformat()
            
            cursor.execute("DELETE FROM alerts WHERE timestamp < ?", (cutoff_date,))
            deleted_alerts = cursor.rowcount
            
            cursor.execute("DELETE FROM crawled_pages WHERE timestamp < ?", (cutoff_date,))
            deleted_pages = cursor.rowcount
            
            # Vacuum to reclaim space
            cursor.execute("VACUUM")
            
            logger.info(f"Cleaned up {deleted_alerts} alerts and {deleted_pages} pages")
    
    def migrate_from_json(self, json_files: Dict[str, str]):
        """Migrate existing JSON data to SQLite"""
        logger.info("🔄 Starting migration from JSON to SQLite...")
        
        # Migrate alerts
        if 'alerts' in json_files and os.path.exists(json_files['alerts']):
            with open(json_files['alerts'], 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            alert_data = json.loads(line)
                            alert = Alert(
                                timestamp=alert_data.get('timestamp', ''),
                                url=alert_data.get('url', ''),
                                title=alert_data.get('title', ''),
                                keywords_found=alert_data.get('keywords_found', []),
                                content_hash=str(hash(alert_data.get('url', '') + str(alert_data.get('keywords_found', [])))),
                                threat_level=self._determine_threat_level(alert_data.get('keywords_found', []))
                            )
                            self.insert_alert(alert)
                        except json.JSONDecodeError:
                            continue
        
        # Migrate visited links
        if 'visited' in json_files and os.path.exists(json_files['visited']):
            with open(json_files['visited'], 'r') as f:
                try:
                    visited_links = json.load(f)
                    for url in visited_links:
                        page = CrawledPage(
                            url=url,
                            timestamp=datetime.now().isoformat(),
                            content_hash=str(hash(url))
                        )
                        self.insert_crawled_page(page)
                except json.JSONDecodeError:
                    pass
        
        logger.info("✅ Migration completed successfully")
    
    def _determine_threat_level(self, keywords: List[str]) -> str:
        """Determine threat level based on keywords"""
        high_risk = ['bomb', 'terror', 'attack', 'kill', 'explosive', 'weapon', 'assassination', 'murder']
        medium_risk = ['carding', 'hacking', 'drugs', 'malware', 'exploit', 'phishing', 'fraud', 'ransomware']
        
        for keyword in keywords:
            if any(risk in keyword.lower() for risk in high_risk):
                return 'HIGH'
            elif any(risk in keyword.lower() for risk in medium_risk):
                return 'MEDIUM'
        
        return 'LOW'
    
    def close(self):
        """Close database connections"""
        if hasattr(self.local, 'connection'):
            self.local.connection.close()

# Global database instance
db_manager = DatabaseManager()

def get_db() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager
