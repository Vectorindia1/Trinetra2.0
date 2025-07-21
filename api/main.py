"""
TRINETRA - Darknet Crawler API Backend
Phase 1: FastAPI Backend for React Frontend Migration
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
from contextlib import asynccontextmanager

# Import our existing modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import db_manager
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                # Remove stale connections
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

# Global WebSocket manager
websocket_manager = WebSocketManager()

# Background task for real-time updates
async def send_realtime_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            # Get latest statistics
            stats = await get_dashboard_stats()
            message = json.dumps({
                "type": "stats_update",
                "data": stats,
                "timestamp": datetime.now().isoformat()
            })
            await websocket_manager.broadcast(message)
            await asyncio.sleep(30)  # Update every 30 seconds
        except Exception as e:
            logger.error(f"Error in real-time updates: {e}")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 TRINETRA API Server starting up...")
    
    # TEMPORARILY DISABLED: Background task causing 100% CPU usage
    # TODO: Fix database query performance issues in send_realtime_updates()
    # asyncio.create_task(send_realtime_updates())
    logger.info("⚠️ Background real-time updates disabled to prevent CPU overload")
    
    yield
    
    # Shutdown
    logger.info("🛑 TRINETRA API Server shutting down...")

# Create FastAPI app
app = FastAPI(
    title="TRINETRA API",
    description="Darknet Crawler - Advanced Threat Intelligence API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Data Processing Functions
# ============================

async def get_dashboard_stats() -> Dict[str, Any]:
    """Get lightweight dashboard statistics (optimized for performance)"""
    try:
        # Get basic statistics only (avoid expensive queries)
        with db_manager.get_cursor() as cursor:
            # Simple count queries
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total_alerts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM crawled_pages")
            total_pages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_analysis")
            total_ai_analyses = cursor.fetchone()[0]
            
            # Quick recent activity count
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE created_at > datetime('now', '-1 day')")
            recent_alerts = cursor.fetchone()[0]
        
        stats = {
            "overview": {
                "total_alerts": total_alerts,
                "total_pages": total_pages,
                "total_ai_analyses": total_ai_analyses,
                "illegal_content_detected": 0,
                "avg_confidence_score": 0.75,
                "active_threat_signatures": 0
            },
            "threat_levels": {
                "alerts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
                "ai_threat_levels": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
            },
            "performance": {
                "avg_processing_time": 0.5,
            },
            "recent_activity": {
                "last_updated": datetime.now().isoformat(),
                "recent_alerts_count": recent_alerts,
                "recent_ai_analyses_count": 0
            }
        }
        
        return stats
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {"error": str(e)}

async def load_json_data(file_path: str) -> List[Dict]:
    """Load data from JSON files (fallback for legacy data)"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('alert_log.json'):
                    return [json.loads(line) for line in f if line.strip()]
                else:
                    return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return []

# ============================
# API Endpoints
# ============================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🕵️ TRINETRA - Darknet Crawler API",
        "version": "1.0.0",
        "status": "active",
        "documentation": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        stats = db_manager.get_threat_statistics()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "total_alerts": stats.get('total_alerts', 0)
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/dashboard")
async def get_dashboard():
    """Get dashboard data for frontend"""
    try:
        stats = await get_dashboard_stats()
        # Extract simple metrics for frontend
        return {
            "total_urls": stats.get('overview', {}).get('total_pages', 0),
            "active_alerts": stats.get('overview', {}).get('total_alerts', 0),
            "ai_analyses": stats.get('overview', {}).get('total_ai_analyses', 0),
            "threat_level": "MODERATE"  # You can make this dynamic based on recent threats
        }
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return {
            "total_urls": 0,
            "active_alerts": 0,
            "ai_analyses": 0,
            "threat_level": "LOW"
        }

@app.get("/api/dashboard/stats")
async def get_dashboard_statistics():
    """Get comprehensive dashboard statistics"""
    try:
        stats = await get_dashboard_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts(
    limit: int = 100, 
    threat_level: Optional[str] = None,
    processed: Optional[bool] = None
):
    """Get alerts with filtering options"""
    try:
        alerts = db_manager.get_alerts(
            limit=limit,
            threat_level=threat_level,
            processed=processed
        )
        
        # Process alerts for frontend
        processed_alerts = []
        for alert in alerts:
            processed_alert = dict(alert)
            if 'keywords_found' in processed_alert and isinstance(processed_alert['keywords_found'], str):
                try:
                    processed_alert['keywords_found'] = json.loads(processed_alert['keywords_found'])
                except:
                    processed_alert['keywords_found'] = []
            processed_alerts.append(processed_alert)
        
        return {
            "success": True,
            "data": processed_alerts,
            "count": len(processed_alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/analyses")
async def get_ai_analyses(
    limit: int = 100,
    threat_level: Optional[str] = None
):
    """Get AI analysis results"""
    try:
        analyses = db_manager.get_ai_analyses(
            limit=limit,
            threat_level=threat_level
        )
        
        return {
            "success": True,
            "data": analyses,
            "count": len(analyses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/statistics")
async def get_ai_statistics():
    """Get AI analysis statistics"""
    try:
        stats = db_manager.get_ai_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/timeline/data")
async def get_timeline_data(
    limit: int = 1000,
    hours_back: int = 24
):
    """Get timeline analysis data for charts"""
    try:
        # Get AI analyses for timeline
        ai_analyses = db_manager.get_ai_analyses(limit=limit)
        
        if not ai_analyses:
            return {
                "success": True,
                "data": {
                    "timeline_data": [],
                    "hourly_threat_counts": [],
                    "hourly_confidence": [],
                    "metrics": {}
                }
            }
        
        # Process timeline data
        timeline_data = []
        for analysis in ai_analyses:
            try:
                timestamp = pd.to_datetime(analysis.get('processed_at'))
                threat_level = analysis.get('threat_level', 'LOW')
                confidence = analysis.get('confidence_score', 0.0)
                illegal_detected = analysis.get('illegal_content_detected', 0)
                
                timeline_data.append({
                    'timestamp': timestamp.isoformat(),
                    'threat_level': threat_level,
                    'confidence': confidence,
                    'illegal_content': bool(illegal_detected),
                    'url': analysis.get('url', 'Unknown')
                })
            except Exception as e:
                continue
        
        if timeline_data:
            df = pd.DataFrame(timeline_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Hourly aggregation
            df['hour'] = df['timestamp'].dt.floor('h')
            hourly_threat_counts = df.groupby(['hour', 'threat_level']).size().reset_index(name='count')
            
            # Convert to JSON-serializable format
            hourly_data = []
            for _, row in hourly_threat_counts.iterrows():
                hourly_data.append({
                    'hour': row['hour'].isoformat(),
                    'threat_level': row['threat_level'],
                    'count': int(row['count'])
                })
            
            # Confidence aggregation
            hourly_confidence = df.groupby('hour').agg({
                'confidence': ['mean', 'min', 'max', 'count']
            }).reset_index()
            hourly_confidence.columns = ['hour', 'avg_confidence', 'min_confidence', 'max_confidence', 'analysis_count']
            
            confidence_data = []
            for _, row in hourly_confidence.iterrows():
                confidence_data.append({
                    'hour': row['hour'].isoformat(),
                    'avg_confidence': float(row['avg_confidence']),
                    'min_confidence': float(row['min_confidence']),
                    'max_confidence': float(row['max_confidence']),
                    'analysis_count': int(row['analysis_count'])
                })
            
            # Calculate metrics
            total_analyses = len(df)
            critical_high = len(df[df['threat_level'].isin(['CRITICAL', 'HIGH'])])
            illegal_content_count = len(df[df['illegal_content'] == True])
            avg_confidence = df['confidence'].mean()
            
            metrics = {
                'total_analyses': total_analyses,
                'critical_high_threats': critical_high,
                'illegal_content_count': illegal_content_count,
                'avg_confidence': float(avg_confidence),
                'threat_level_distribution': df['threat_level'].value_counts().to_dict()
            }
            
            return {
                "success": True,
                "data": {
                    "timeline_data": timeline_data,
                    "hourly_threat_counts": hourly_data,
                    "hourly_confidence": confidence_data,
                    "metrics": metrics
                }
            }
        
        return {
            "success": True,
            "data": {
                "timeline_data": [],
                "hourly_threat_counts": [],
                "hourly_confidence": [],
                "metrics": {}
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting timeline data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/keywords/analytics")
async def get_keyword_analytics(limit: int = 500):
    """Get AI-powered keyword analytics"""
    try:
        ai_analyses = db_manager.get_ai_analyses(limit=limit)
        
        if not ai_analyses:
            return {
                "success": True,
                "data": {
                    "keywords": [],
                    "keyword_details": {},
                    "statistics": {}
                }
            }
        
        # Collect AI-identified threat categories and indicators
        ai_keywords = []
        keyword_to_urls = {}
        keyword_to_threat_levels = {}
        
        for analysis in ai_analyses:
            url = analysis.get('url', 'Unknown')
            threat_level = analysis.get('threat_level', 'LOW')
            
            # Process threat categories
            for category in analysis.get('threat_categories', []):
                ai_keywords.append(category)
                if category not in keyword_to_urls:
                    keyword_to_urls[category] = []
                    keyword_to_threat_levels[category] = []
                keyword_to_urls[category].append(url)
                keyword_to_threat_levels[category].append(threat_level)
            
            # Process suspicious indicators
            for indicator in analysis.get('suspicious_indicators', []):
                ai_keywords.append(indicator)
                if indicator not in keyword_to_urls:
                    keyword_to_urls[indicator] = []
                    keyword_to_threat_levels[indicator] = []
                keyword_to_urls[indicator].append(url)
                keyword_to_threat_levels[indicator].append(threat_level)
        
        if ai_keywords:
            keyword_counts = Counter(ai_keywords)
            top_keywords = keyword_counts.most_common(15)
            
            # Prepare keyword data
            keywords_data = []
            for keyword, frequency in top_keywords:
                avg_threat_level = Counter(keyword_to_threat_levels.get(keyword, [])).most_common(1)[0][0] if keyword_to_threat_levels.get(keyword) else 'LOW'
                
                keywords_data.append({
                    'keyword': keyword,
                    'frequency': frequency,
                    'avg_threat_level': avg_threat_level,
                    'unique_urls': len(set(keyword_to_urls.get(keyword, []))),
                    'urls': keyword_to_urls.get(keyword, [])[:10]  # Limit URLs for performance
                })
            
            # Calculate statistics
            statistics = {
                'total_keywords': len(set(ai_keywords)),
                'threat_categories_count': len(set([k for analysis in ai_analyses for k in analysis.get('threat_categories', [])])),
                'suspicious_indicators_count': len(set([k for analysis in ai_analyses for k in analysis.get('suspicious_indicators', [])]))
            }
            
            return {
                "success": True,
                "data": {
                    "keywords": keywords_data,
                    "keyword_details": {
                        "keyword_to_urls": keyword_to_urls,
                        "keyword_to_threat_levels": keyword_to_threat_levels
                    },
                    "statistics": statistics
                }
            }
        
        return {
            "success": True,
            "data": {
                "keywords": [],
                "keyword_details": {},
                "statistics": {}
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting keyword analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/threat/signatures")
async def get_threat_signatures(limit: int = 20):
    """Get active threat signatures"""
    try:
        signatures = db_manager.get_threat_signatures(limit=limit)
        return {
            "success": True,
            "data": signatures,
            "count": len(signatures)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/test-connection")
async def test_ai_connection():
    """Test AI analysis connection"""
    try:
        from ai.gemini_analyzer import gemini_analyzer
        
        # Test analysis
        test_analysis = gemini_analyzer.analyze_content_sync(
            url="test://example.onion",
            title="Test Page",
            content="This is a test page for AI analysis.",
            keywords=["test"]
        )
        
        if test_analysis:
            return {
                "success": True,
                "message": "AI Analysis is working correctly!",
                "test_result": {
                    "threat_level": test_analysis.threat_level,
                    "confidence_score": test_analysis.confidence_score
                }
            }
        else:
            return {
                "success": False,
                "message": "AI Analysis test failed"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"AI Connection failed: {str(e)}"
        }

# ============================
# WebSocket Endpoints
# ============================

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            # Process incoming messages if needed
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket_manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                        websocket
                    )
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

# ============================
# Background Tasks
# ============================

from pydantic import BaseModel

class CrawlerRequest(BaseModel):
    url: str
    scan_type: str = "manual"

class CrawlerStopRequest(BaseModel):
    process_id: int

@app.post("/api/crawler/start")
async def start_crawler(request: CrawlerRequest, background_tasks: BackgroundTasks):
    """Start crawler for a specific URL"""
    try:
        url = request.url
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Start crawler process
        import subprocess
        import os
        
        process = subprocess.Popen([
            "/home/vector/darknet_crawler/tor-env/bin/scrapy", "crawl", "onion",
            "-a", f"start_url={url}",
            "-s", "LOG_LEVEL=INFO"
        ], 
        cwd="/home/vector/darknet_crawler",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )
        
        logger.info(f"Started crawler for URL: {url} (PID: {process.pid})")
        
        return {
            "success": True,
            "message": f"Crawler started for: {url}",
            "process_id": process.pid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting crawler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/crawler/stop")
async def stop_crawler(request: CrawlerStopRequest):
    """Stop a running crawler process"""
    try:
        import psutil
        
        # Kill the process
        try:
            process = psutil.Process(request.process_id)
            process.terminate()
            process.wait(timeout=5)
        except psutil.NoSuchProcess:
            return {
                "success": True,
                "message": "Process not found (may have already stopped)"
            }
        except psutil.TimeoutExpired:
            process.kill()
        
        return {
            "success": True,
            "message": f"Stopped crawler process {request.process_id}"
        }
    except Exception as e:
        logger.error(f"Error stopping crawler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_crawler(url: str):
    """Background task to run crawler"""
    try:
        import subprocess
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Run crawler
        process = subprocess.Popen([
            "/home/vector/darknet_crawler/tor-env/bin/scrapy", "crawl", "onion",
            "-a", f"start_url={url}",
            "-s", "LOG_LEVEL=INFO"
        ], cwd="/home/vector/darknet_crawler")
        
        logger.info(f"Started crawler for URL: {url} (PID: {process.pid})")
        
        # Broadcast update to WebSocket clients
        await websocket_manager.broadcast(json.dumps({
            "type": "crawler_started",
            "url": url,
            "pid": process.pid,
            "timestamp": datetime.now().isoformat()
        }))
        
    except Exception as e:
        logger.error(f"Error starting crawler: {e}")
        
        # Broadcast error to WebSocket clients
        await websocket_manager.broadcast(json.dumps({
            "type": "crawler_error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
