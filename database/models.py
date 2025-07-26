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
                
                # Chatroom links table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chatroom_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_url TEXT NOT NULL,
                        chatroom_url TEXT NOT NULL,
                        chatroom_type TEXT,
                        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        investigated BOOLEAN DEFAULT FALSE,
                        notes TEXT
                    )
                """)
                
                # AI Analysis results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_hash TEXT UNIQUE NOT NULL,
                        url TEXT NOT NULL,
                        threat_level TEXT NOT NULL,
                        threat_categories TEXT,
                        suspicious_indicators TEXT,
                        illegal_content_detected BOOLEAN DEFAULT FALSE,
                        confidence_score REAL DEFAULT 0.0,
                        analysis_summary TEXT,
                        recommended_actions TEXT,
                        ai_reasoning TEXT,
                        threat_signature TEXT,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Threat intelligence enhanced table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS threat_signatures (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        signature_hash TEXT UNIQUE NOT NULL,
                        threat_type TEXT NOT NULL,
                        indicators TEXT NOT NULL,
                        confidence_level REAL DEFAULT 0.0,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        occurrence_count INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'ACTIVE',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Link relationships table for graph mapping
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS link_relationships (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_url TEXT NOT NULL,
                        target_url TEXT NOT NULL,
                        relationship_type TEXT DEFAULT 'link',
                        discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        occurrence_count INTEGER DEFAULT 1,
                        link_text TEXT,
                        link_position INTEGER,
                        is_external BOOLEAN DEFAULT FALSE,
                        UNIQUE(source_url, target_url)
                    )
                """)
                
                # Node metadata for graph visualization
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS graph_nodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT UNIQUE NOT NULL,
                        title TEXT,
                        node_type TEXT DEFAULT 'page',
                        threat_level TEXT DEFAULT 'LOW',
                        discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_crawled TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        page_size INTEGER DEFAULT 0,
                        incoming_links INTEGER DEFAULT 0,
                        outgoing_links INTEGER DEFAULT 0,
                        centrality_score REAL DEFAULT 0.0,
                        cluster_id INTEGER,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Batch system tables
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scan_batches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT UNIQUE NOT NULL,
                        batch_name TEXT NOT NULL,
                        description TEXT,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        status TEXT DEFAULT 'RUNNING',
                        total_urls INTEGER DEFAULT 0,
                        completed_urls INTEGER DEFAULT 0,
                        failed_urls INTEGER DEFAULT 0,
                        alerts_generated INTEGER DEFAULT 0,
                        ai_analyses_count INTEGER DEFAULT 0,
                        batch_config TEXT,
                        created_by TEXT DEFAULT 'system',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scan_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT NOT NULL REFERENCES scan_batches(batch_id),
                        scan_id TEXT UNIQUE NOT NULL,
                        url TEXT NOT NULL,
                        scan_type TEXT DEFAULT 'web_crawl',
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        status TEXT DEFAULT 'RUNNING',
                        pages_crawled INTEGER DEFAULT 0,
                        alerts_found INTEGER DEFAULT 0,
                        ai_analysis_id INTEGER,
                        response_code INTEGER,
                        error_message TEXT,
                        processing_time REAL DEFAULT 0.0,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (ai_analysis_id) REFERENCES ai_analysis(id)
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS batch_urls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        batch_id TEXT NOT NULL REFERENCES scan_batches(batch_id),
                        url TEXT NOT NULL,
                        priority INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'PENDING',
                        assigned_scan_id TEXT,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        result_summary TEXT,
                        FOREIGN KEY (assigned_scan_id) REFERENCES scan_history(scan_id)
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
                    "CREATE INDEX IF NOT EXISTS idx_link_source ON link_relationships(source_url)",
                    "CREATE INDEX IF NOT EXISTS idx_link_target ON link_relationships(target_url)",
                    "CREATE INDEX IF NOT EXISTS idx_link_last_seen ON link_relationships(last_seen)",
                    "CREATE INDEX IF NOT EXISTS idx_graph_nodes_url ON graph_nodes(url)",
                    "CREATE INDEX IF NOT EXISTS idx_graph_nodes_threat ON graph_nodes(threat_level)",
                    "CREATE INDEX IF NOT EXISTS idx_graph_nodes_centrality ON graph_nodes(centrality_score)",
                    "CREATE INDEX IF NOT EXISTS idx_graph_nodes_active ON graph_nodes(is_active)",
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
    
    def insert_ai_analysis(self, analysis_data: Dict) -> int:
        """Insert AI analysis results"""
        with self.get_cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO ai_analysis 
                    (content_hash, url, threat_level, threat_categories, suspicious_indicators,
                     illegal_content_detected, confidence_score, analysis_summary, 
                     recommended_actions, ai_reasoning, threat_signature)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis_data.get('content_hash', ''),
                    analysis_data.get('url', ''),
                    analysis_data.get('threat_level', 'LOW'),
                    json.dumps(analysis_data.get('threat_categories', [])),
                    json.dumps(analysis_data.get('suspicious_indicators', [])),
                    analysis_data.get('illegal_content_detected', False),
                    analysis_data.get('confidence_score', 0.0),
                    analysis_data.get('analysis_summary', ''),
                    json.dumps(analysis_data.get('recommended_actions', [])),
                    analysis_data.get('ai_reasoning', ''),
                    analysis_data.get('threat_signature', '')
                ))
                return cursor.lastrowid
            except sqlite3.Error as e:
                logger.error(f"Error inserting AI analysis: {e}")
                return 0
    
    def get_ai_analyses(self, limit: int = 100, threat_level: str = None) -> List[Dict]:
        """Get AI analysis results"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM ai_analysis WHERE 1=1"
            params = []
            
            if threat_level:
                query += " AND threat_level = ?"
                params.append(threat_level)
            
            query += " ORDER BY processed_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                # Parse JSON fields
                try:
                    result['threat_categories'] = json.loads(result.get('threat_categories', '[]'))
                    result['suspicious_indicators'] = json.loads(result.get('suspicious_indicators', '[]'))
                    result['recommended_actions'] = json.loads(result.get('recommended_actions', '[]'))
                except json.JSONDecodeError:
                    pass
                results.append(result)
            
            return results
    
    def get_threat_signatures(self, limit: int = 50) -> List[Dict]:
        """Get threat signatures"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM threat_signatures 
                WHERE status = 'ACTIVE'
                ORDER BY occurrence_count DESC, last_seen DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_threat_signature(self, signature_hash: str, threat_type: str, indicators: List[str], confidence: float):
        """Update or insert threat signature"""
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO threat_signatures (signature_hash, threat_type, indicators, confidence_level)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(signature_hash) DO UPDATE SET
                    threat_type = excluded.threat_type,
                    indicators = excluded.indicators,
                    confidence_level = excluded.confidence_level,
                    last_seen = CURRENT_TIMESTAMP,
                    occurrence_count = occurrence_count + 1
            """, (signature_hash, threat_type, json.dumps(indicators), confidence))
    
    def get_ai_statistics(self) -> Dict:
        """Get AI analysis statistics"""
        with self.get_cursor() as cursor:
            stats = {}
            
            # AI analysis statistics
            cursor.execute("SELECT COUNT(*) FROM ai_analysis")
            stats['total_ai_analyses'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT threat_level, COUNT(*) FROM ai_analysis GROUP BY threat_level")
            stats['ai_threat_levels'] = dict(cursor.fetchall())
            
            cursor.execute("SELECT COUNT(*) FROM ai_analysis WHERE illegal_content_detected = 1")
            stats['illegal_content_detected'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(confidence_score) FROM ai_analysis")
            stats['avg_confidence_score'] = cursor.fetchone()[0] or 0.0
            
            # Threat signature statistics
            cursor.execute("SELECT COUNT(*) FROM threat_signatures WHERE status = 'ACTIVE'")
            stats['active_threat_signatures'] = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT threat_type, COUNT(*) 
                FROM threat_signatures 
                WHERE status = 'ACTIVE' 
                GROUP BY threat_type 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            stats['top_threat_types'] = dict(cursor.fetchall())
            
            return stats
    
    def insert_link_relationship(self, source_url: str, target_url: str, link_text: str = None, link_position: int = None) -> int:
        """Insert or update link relationship"""
        with self.get_cursor() as cursor:
            try:
                is_external = not ('.onion' in target_url and '.onion' in source_url)
                cursor.execute("""
                    INSERT INTO link_relationships 
                    (source_url, target_url, link_text, link_position, is_external)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(source_url, target_url) DO UPDATE SET
                        last_seen = CURRENT_TIMESTAMP,
                        occurrence_count = occurrence_count + 1,
                        link_text = COALESCE(excluded.link_text, link_text)
                """, (source_url, target_url, link_text, link_position, is_external))
                return cursor.lastrowid
            except sqlite3.Error as e:
                logger.error(f"Error inserting link relationship: {e}")
                return 0
    
    def upsert_graph_node(self, url: str, title: str = None, node_type: str = 'page', 
                         threat_level: str = 'LOW', page_size: int = 0) -> int:
        """Insert or update graph node"""
        with self.get_cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT INTO graph_nodes 
                    (url, title, node_type, threat_level, page_size, last_crawled)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(url) DO UPDATE SET
                        title = COALESCE(excluded.title, title),
                        node_type = excluded.node_type,
                        threat_level = excluded.threat_level,
                        page_size = excluded.page_size,
                        last_crawled = CURRENT_TIMESTAMP
                """, (url, title, node_type, threat_level, page_size))
                
                # Update link counts
                cursor.execute("""
                    UPDATE graph_nodes SET 
                        outgoing_links = (SELECT COUNT(*) FROM link_relationships WHERE source_url = ?),
                        incoming_links = (SELECT COUNT(*) FROM link_relationships WHERE target_url = ?)
                    WHERE url = ?
                """, (url, url, url))
                
                return cursor.lastrowid
            except sqlite3.Error as e:
                logger.error(f"Error upserting graph node: {e}")
                return 0
    
    def get_graph_data(self, limit: int = 1000, threat_filter: List[str] = None) -> Dict:
        """Get graph data for visualization"""
        with self.get_cursor() as cursor:
            # Get nodes with filtering
            node_query = "SELECT * FROM graph_nodes WHERE is_active = 1"
            params = []
            
            if threat_filter:
                placeholders = ','.join(['?' for _ in threat_filter])
                node_query += f" AND threat_level IN ({placeholders})"
                params.extend(threat_filter)
            
            node_query += " ORDER BY centrality_score DESC, incoming_links DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(node_query, params)
            nodes = [dict(row) for row in cursor.fetchall()]
            
            # Get node URLs for relationship filtering
            if nodes:
                node_urls = [node['url'] for node in nodes]
                url_placeholders = ','.join(['?' for _ in node_urls])
                
                # Get relationships between these nodes
                cursor.execute(f"""
                    SELECT lr.*, 
                           sn.threat_level as source_threat,
                           tn.threat_level as target_threat
                    FROM link_relationships lr
                    JOIN graph_nodes sn ON lr.source_url = sn.url
                    JOIN graph_nodes tn ON lr.target_url = tn.url
                    WHERE lr.source_url IN ({url_placeholders}) 
                       OR lr.target_url IN ({url_placeholders})
                    ORDER BY lr.occurrence_count DESC
                """, node_urls + node_urls)
                
                edges = [dict(row) for row in cursor.fetchall()]
            else:
                edges = []
            
            return {
                'nodes': nodes,
                'edges': edges,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'external_links': len([e for e in edges if e['is_external']]),
                    'internal_links': len([e for e in edges if not e['is_external']])
                }
            }
    
    def calculate_centrality_scores(self):
        """Calculate and update centrality scores for nodes"""
        with self.get_cursor() as cursor:
            # Simple centrality calculation based on incoming/outgoing links
            cursor.execute("""
                UPDATE graph_nodes 
                SET centrality_score = (
                    (incoming_links * 1.5) + outgoing_links + 
                    CASE 
                        WHEN threat_level = 'CRITICAL' THEN 10
                        WHEN threat_level = 'HIGH' THEN 5
                        WHEN threat_level = 'MEDIUM' THEN 2
                        ELSE 0
                    END
                ) / 10.0
                WHERE is_active = 1
            """)
            
            # Update cluster assignments (simple clustering by domain)
            cursor.execute("""
                UPDATE graph_nodes 
                SET cluster_id = (LENGTH(SUBSTR(url, INSTR(url, '://') + 3, 
                                         INSTR(SUBSTR(url, INSTR(url, '://') + 3), '/') - 1)) * 7 + 
                                 UNICODE(SUBSTR(url, INSTR(url, '://') + 3, 1))) % 20
                WHERE is_active = 1
            """)
            
            logger.info("✅ Centrality scores and clusters updated")
    
    def get_link_map_statistics(self) -> Dict:
        """Get statistics for the link map"""
        with self.get_cursor() as cursor:
            stats = {}
            
            # Node statistics
            cursor.execute("SELECT COUNT(*) FROM graph_nodes WHERE is_active = 1")
            stats['total_nodes'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT threat_level, COUNT(*) FROM graph_nodes WHERE is_active = 1 GROUP BY threat_level")
            stats['nodes_by_threat'] = dict(cursor.fetchall())
            
            cursor.execute("SELECT node_type, COUNT(*) FROM graph_nodes WHERE is_active = 1 GROUP BY node_type")
            stats['nodes_by_type'] = dict(cursor.fetchall())
            
            # Relationship statistics
            cursor.execute("SELECT COUNT(*) FROM link_relationships")
            stats['total_relationships'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM link_relationships WHERE is_external = 1")
            stats['external_links'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM link_relationships WHERE is_external = 0")
            stats['internal_links'] = cursor.fetchone()[0]
            
            # Top connected nodes
            cursor.execute("""
                SELECT url, title, incoming_links, outgoing_links, centrality_score, threat_level
                FROM graph_nodes 
                WHERE is_active = 1
                ORDER BY centrality_score DESC 
                LIMIT 10
            """)
            stats['top_nodes'] = [dict(row) for row in cursor.fetchall()]
            
            # Recent discoveries
            cursor.execute("""
                SELECT url, title, threat_level, discovery_date
                FROM graph_nodes 
                WHERE is_active = 1
                ORDER BY discovery_date DESC 
                LIMIT 20
            """)
            stats['recent_nodes'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    # ============================
    # BATCH SYSTEM METHODS
    # ============================
    
    def create_batch(self, batch_name: str, description: str = None, urls: List[str] = None, batch_config: Dict = None, created_by: str = "system") -> str:
        """Create a new scan batch"""
        import uuid
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO scan_batches 
                (batch_id, batch_name, description, total_urls, batch_config, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                batch_id,
                batch_name,
                description,
                len(urls) if urls else 0,
                json.dumps(batch_config) if batch_config else None,
                created_by
            ))
            
            # Add URLs to batch if provided
            if urls:
                for i, url in enumerate(urls):
                    cursor.execute("""
                        INSERT INTO batch_urls (batch_id, url, priority)
                        VALUES (?, ?, ?)
                    """, (batch_id, url, i + 1))
            
            logger.info(f"✅ Created batch {batch_id} with {len(urls) if urls else 0} URLs")
            return batch_id
    
    def get_batches(self, limit: int = 50, status: str = None) -> List[Dict]:
        """Get scan batches"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM scan_batches WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                # Parse batch_config JSON
                try:
                    if result.get('batch_config'):
                        result['batch_config'] = json.loads(result['batch_config'])
                except json.JSONDecodeError:
                    result['batch_config'] = {}
                results.append(result)
            
            return results
    
    def get_batch_details(self, batch_id: str) -> Optional[Dict]:
        """Get detailed information about a specific batch"""
        with self.get_cursor() as cursor:
            # Get batch info
            cursor.execute("SELECT * FROM scan_batches WHERE batch_id = ?", (batch_id,))
            batch_row = cursor.fetchone()
            
            if not batch_row:
                return None
            
            batch = dict(batch_row)
            
            # Parse batch_config
            try:
                if batch.get('batch_config'):
                    batch['batch_config'] = json.loads(batch['batch_config'])
            except json.JSONDecodeError:
                batch['batch_config'] = {}
            
            # Get batch URLs status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM batch_urls 
                WHERE batch_id = ?
                GROUP BY status
            """, (batch_id,))
            batch['url_status_counts'] = dict(cursor.fetchall())
            
            # Get scan history for this batch
            cursor.execute("""
                SELECT * FROM scan_history 
                WHERE batch_id = ?
                ORDER BY start_time DESC
            """, (batch_id,))
            batch['scan_history'] = [dict(row) for row in cursor.fetchall()]
            
            # Get recent alerts from this batch
            cursor.execute("""
                SELECT a.* FROM alerts a
                JOIN scan_history sh ON a.url = sh.url
                WHERE sh.batch_id = ?
                ORDER BY a.timestamp DESC
                LIMIT 10
            """, (batch_id,))
            batch['recent_alerts'] = [dict(row) for row in cursor.fetchall()]
            
            return batch
    
    def start_scan(self, batch_id: str, url: str, scan_type: str = "web_crawl") -> str:
        """Start a new scan within a batch"""
        import uuid
        scan_id = f"scan_{uuid.uuid4().hex[:8]}"
        
        with self.get_cursor() as cursor:
            # Insert scan record
            cursor.execute("""
                INSERT INTO scan_history 
                (batch_id, scan_id, url, scan_type)
                VALUES (?, ?, ?, ?)
            """, (batch_id, scan_id, url, scan_type))
            
            # Update batch URL status
            cursor.execute("""
                UPDATE batch_urls 
                SET status = 'RUNNING', assigned_scan_id = ?, started_at = CURRENT_TIMESTAMP
                WHERE batch_id = ? AND url = ?
            """, (scan_id, batch_id, url))
            
            return scan_id
    
    def complete_scan(self, scan_id: str, status: str = "COMPLETED", pages_crawled: int = 0, 
                     alerts_found: int = 0, ai_analysis_id: Optional[int] = None, 
                     response_code: Optional[int] = None, error_message: Optional[str] = None,
                     processing_time: float = 0.0, metadata: Optional[Dict] = None):
        """Complete a scan and update statistics"""
        with self.get_cursor() as cursor:
            # Update scan record
            cursor.execute("""
                UPDATE scan_history 
                SET end_time = CURRENT_TIMESTAMP, status = ?, pages_crawled = ?, 
                    alerts_found = ?, ai_analysis_id = ?, response_code = ?, 
                    error_message = ?, processing_time = ?, metadata = ?
                WHERE scan_id = ?
            """, (
                status, pages_crawled, alerts_found, ai_analysis_id, 
                response_code, error_message, processing_time,
                json.dumps(metadata) if metadata else None,
                scan_id
            ))
            
            # Get batch_id and url for this scan
            cursor.execute("SELECT batch_id, url FROM scan_history WHERE scan_id = ?", (scan_id,))
            scan_info = cursor.fetchone()
            
            if scan_info:
                batch_id, url = scan_info
                
                # Update batch URL status
                url_status = "COMPLETED" if status == "COMPLETED" else "FAILED"
                cursor.execute("""
                    UPDATE batch_urls 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP,
                        result_summary = ?
                    WHERE batch_id = ? AND url = ?
                """, (
                    url_status, 
                    f"Crawled {pages_crawled} pages, {alerts_found} alerts",
                    batch_id, url
                ))
                
                # Update batch statistics
                cursor.execute("""
                    UPDATE scan_batches 
                    SET completed_urls = completed_urls + 1,
                        failed_urls = CASE WHEN ? = 'FAILED' THEN failed_urls + 1 ELSE failed_urls END,
                        alerts_generated = alerts_generated + ?,
                        ai_analyses_count = CASE WHEN ? IS NOT NULL THEN ai_analyses_count + 1 ELSE ai_analyses_count END
                    WHERE batch_id = ?
                """, (status, alerts_found, ai_analysis_id, batch_id))
                
                # Check if batch is complete
                cursor.execute("""
                    SELECT total_urls, completed_urls + failed_urls as processed_urls
                    FROM scan_batches 
                    WHERE batch_id = ?
                """, (batch_id,))
                
                batch_progress = cursor.fetchone()
                if batch_progress and batch_progress[0] <= batch_progress[1]:
                    # Batch is complete
                    cursor.execute("""
                        UPDATE scan_batches 
                        SET status = 'COMPLETED', end_time = CURRENT_TIMESTAMP
                        WHERE batch_id = ?
                    """, (batch_id,))
                    logger.info(f"✅ Batch {batch_id} completed")
    
    def get_batch_statistics(self) -> Dict:
        """Get comprehensive batch system statistics"""
        with self.get_cursor() as cursor:
            stats = {}
            
            # Total batches
            cursor.execute("SELECT COUNT(*) FROM scan_batches")
            stats['total_batches'] = cursor.fetchone()[0]
            
            # Batches by status
            cursor.execute("SELECT status, COUNT(*) FROM scan_batches GROUP BY status")
            stats['batches_by_status'] = dict(cursor.fetchall())
            
            # Total scans
            cursor.execute("SELECT COUNT(*) FROM scan_history")
            stats['total_scans'] = cursor.fetchone()[0]
            
            # Scans by status
            cursor.execute("SELECT status, COUNT(*) FROM scan_history GROUP BY status")
            stats['scans_by_status'] = dict(cursor.fetchall())
            
            # URLs by status
            cursor.execute("SELECT status, COUNT(*) FROM batch_urls GROUP BY status")
            stats['urls_by_status'] = dict(cursor.fetchall())
            
            # Average processing time
            cursor.execute("SELECT AVG(processing_time) FROM scan_history WHERE processing_time > 0")
            stats['avg_processing_time'] = cursor.fetchone()[0] or 0.0
            
            # Recent batch activity
            cursor.execute("""
                SELECT batch_name, status, created_at, total_urls, completed_urls, alerts_generated
                FROM scan_batches 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            stats['recent_batches'] = [dict(row) for row in cursor.fetchall()]
            
            # Top performing batches (by alerts generated)
            cursor.execute("""
                SELECT batch_name, alerts_generated, total_urls, 
                       ROUND(CAST(alerts_generated AS FLOAT) / total_urls * 100, 2) as alert_rate
                FROM scan_batches 
                WHERE total_urls > 0 AND status = 'COMPLETED'
                ORDER BY alert_rate DESC 
                LIMIT 5
            """)
            stats['top_alert_batches'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def get_scan_history(self, batch_id: str = None, limit: int = 100) -> List[Dict]:
        """Get scan history with optional batch filtering"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM scan_history WHERE 1=1"
            params = []
            
            if batch_id:
                query += " AND batch_id = ?"
                params.append(batch_id)
            
            query += " ORDER BY start_time DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                result = dict(row)
                # Parse metadata JSON
                try:
                    if result.get('metadata'):
                        result['metadata'] = json.loads(result['metadata'])
                except json.JSONDecodeError:
                    result['metadata'] = {}
                results.append(result)
            
            return results
    
    def add_urls_to_batch(self, batch_id: str, urls: List[str]) -> int:
        """Add URLs to an existing batch"""
        with self.get_cursor() as cursor:
            added_count = 0
            
            # Get current max priority for this batch
            cursor.execute(
                "SELECT COALESCE(MAX(priority), 0) FROM batch_urls WHERE batch_id = ?", 
                (batch_id,)
            )
            max_priority = cursor.fetchone()[0]
            
            for url in urls:
                try:
                    max_priority += 1
                    cursor.execute("""
                        INSERT INTO batch_urls (batch_id, url, priority)
                        VALUES (?, ?, ?)
                    """, (batch_id, url, max_priority))
                    added_count += 1
                except sqlite3.IntegrityError:
                    # URL already exists in batch, skip
                    continue
            
            # Update batch total_urls count
            cursor.execute("""
                UPDATE scan_batches 
                SET total_urls = total_urls + ?
                WHERE batch_id = ?
            """, (added_count, batch_id))
            
            logger.info(f"✅ Added {added_count} URLs to batch {batch_id}")
            return added_count
    
    def delete_batch(self, batch_id: str) -> bool:
        """Delete a batch and all associated data"""
        with self.get_cursor() as cursor:
            try:
                # Delete in order due to foreign key constraints
                cursor.execute("DELETE FROM batch_urls WHERE batch_id = ?", (batch_id,))
                cursor.execute("DELETE FROM scan_history WHERE batch_id = ?", (batch_id,))
                cursor.execute("DELETE FROM scan_batches WHERE batch_id = ?", (batch_id,))
                
                logger.info(f"✅ Deleted batch {batch_id}")
                return True
            except sqlite3.Error as e:
                logger.error(f"Error deleting batch {batch_id}: {e}")
                return False
    
    def get_pending_urls(self, batch_id: str = None, limit: int = 100) -> List[Dict]:
        """Get pending URLs for scanning"""
        with self.get_cursor() as cursor:
            query = "SELECT * FROM batch_urls WHERE status = 'PENDING'"
            params = []
            
            if batch_id:
                query += " AND batch_id = ?"
                params.append(batch_id)
            
            query += " ORDER BY priority ASC, added_at ASC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_pending_batch_urls(self, batch_id: str) -> List[Dict]:
        """Get pending URLs for a specific batch"""
        return self.get_pending_urls(batch_id=batch_id)
    
    def update_batch_status(self, batch_id: str, status: str):
        """Update batch status"""
        with self.get_cursor() as cursor:
            if status == 'COMPLETED':
                cursor.execute("""
                    UPDATE scan_batches 
                    SET status = ?, end_time = CURRENT_TIMESTAMP
                    WHERE batch_id = ?
                """, (status, batch_id))
            elif status == 'RUNNING':
                cursor.execute("""
                    UPDATE scan_batches 
                    SET status = ?, start_time = CURRENT_TIMESTAMP
                    WHERE batch_id = ?
                """, (status, batch_id))
            else:
                cursor.execute("""
                    UPDATE scan_batches 
                    SET status = ?
                    WHERE batch_id = ?
                """, (status, batch_id))
            
            logger.info(f"✅ Updated batch {batch_id} status to {status}")

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
    
    def get_threat_trends(self, days: int = 30) -> Dict:
        """Get threat trend analytics"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        DATE(created_at) as date,
                        threat_level,
                        COUNT(*) as count
                    FROM alerts 
                    WHERE created_at > datetime('now', '-{days} days')
                    GROUP BY DATE(created_at), threat_level
                    ORDER BY date DESC
                """)
                
                trends = {}
                for row in cursor.fetchall():
                    date, threat_level, count = row
                    if date not in trends:
                        trends[date] = {}
                    trends[date][threat_level] = count
                
                return trends
        except Exception as e:
            logger.error(f"Error getting threat trends: {e}")
            return {}
    
    def get_geographical_analytics(self) -> List[Dict]:
        """Get geographical distribution of threats"""
        try:
            # This would integrate with actual geolocation data
            # For now, return placeholder data
            return [
                {"country": "Unknown", "threat_count": 0, "confidence": 0.0}
            ]
        except Exception as e:
            logger.error(f"Error getting geographical analytics: {e}")
            return []
    
    def get_crawling_performance(self) -> Dict:
        """Get crawling performance metrics"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        AVG(processing_time) as avg_processing_time,
                        COUNT(*) as total_pages,
                        AVG(page_size) as avg_page_size
                    FROM crawled_pages
                    WHERE created_at > datetime('now', '-7 days')
                """)
                
                row = cursor.fetchone()
                if row:
                    return {
                        "avg_processing_time": row[0] or 0.0,
                        "total_pages": row[1],
                        "avg_page_size": row[2] or 0
                    }
                return {"avg_processing_time": 0.0, "total_pages": 0, "avg_page_size": 0}
        except Exception as e:
            logger.error(f"Error getting crawling performance: {e}")
            return {"avg_processing_time": 0.0, "total_pages": 0, "avg_page_size": 0}
    
    def get_ai_performance(self) -> Dict:
        """Get AI analysis performance metrics"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        AVG(confidence_score) as avg_confidence,
                        COUNT(*) as total_analyses,
                        COUNT(CASE WHEN threat_level = 'HIGH' OR threat_level = 'CRITICAL' THEN 1 END) as high_threat_count
                    FROM ai_analysis
                    WHERE created_at > datetime('now', '-7 days')
                """)
                
                row = cursor.fetchone()
                if row:
                    return {
                        "avg_confidence": row[0] or 0.0,
                        "total_analyses": row[1],
                        "high_threat_count": row[2] or 0
                    }
                return {"avg_confidence": 0.0, "total_analyses": 0, "high_threat_count": 0}
        except Exception as e:
            logger.error(f"Error getting AI performance: {e}")
            return {"avg_confidence": 0.0, "total_analyses": 0, "high_threat_count": 0}
    
    def get_alert_processing_time(self) -> float:
        """Get average alert processing time"""
        try:
            # This would calculate actual processing time
            # For now, return a placeholder value
            return 1.2  # seconds
        except Exception as e:
            logger.error(f"Error getting alert processing time: {e}")
            return 0.0
    
    def get_database_size(self) -> Dict:
        """Get database size information"""
        try:
            import os
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            return {
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Error getting database size: {e}")
            return {"size_bytes": 0, "size_mb": 0}
    
    def get_ai_analyses(self, limit: int = 100, threat_level: str = None) -> List[Dict]:
        """Get AI analysis results"""
        try:
            with self.get_cursor() as cursor:
                query = "SELECT * FROM ai_analysis WHERE 1=1"
                params = []
                
                if threat_level:
                    query += " AND threat_level = ?"
                    params.append(threat_level)
                
                query += " ORDER BY processed_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting AI analyses: {e}")
            return []
    
    def get_ai_statistics(self) -> Dict:
        """Get AI analysis statistics"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_analyses,
                        AVG(confidence_score) as avg_confidence,
                        COUNT(CASE WHEN threat_level = 'CRITICAL' THEN 1 END) as critical_count,
                        COUNT(CASE WHEN threat_level = 'HIGH' THEN 1 END) as high_count,
                        COUNT(CASE WHEN illegal_content_detected = 1 THEN 1 END) as illegal_content_count
                    FROM ai_analysis
                """)
                
                row = cursor.fetchone()
                if row:
                    return {
                        "total_analyses": row[0],
                        "avg_confidence": row[1] or 0.0,
                        "critical_count": row[2],
                        "high_count": row[3],
                        "illegal_content_count": row[4]
                    }
                return {
                    "total_analyses": 0,
                    "avg_confidence": 0.0,
                    "critical_count": 0,
                    "high_count": 0,
                    "illegal_content_count": 0
                }
        except Exception as e:
            logger.error(f"Error getting AI statistics: {e}")
            return {
                "total_analyses": 0,
                "avg_confidence": 0.0,
                "critical_count": 0,
                "high_count": 0,
                "illegal_content_count": 0
            }
    
    def get_threat_signatures(self, limit: int = 20) -> List[Dict]:
        """Get active threat signatures"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM threat_signatures 
                    WHERE status = 'ACTIVE'
                    ORDER BY last_seen DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting threat signatures: {e}")
            return []

# Global database instance
db_manager = DatabaseManager()

def get_db() -> DatabaseManager:
    """Get database manager instance"""
    return db_manager
