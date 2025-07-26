#!/usr/bin/env python3
"""
Real-time WebSocket notification service for TRINETRA
Broadcasts live updates to the dashboard as data is scraped and analyzed
"""

import json
import asyncio
import websockets
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealtimeNotifier:
    """
    Service for broadcasting real-time updates to WebSocket clients
    """
    
    def __init__(self, api_websocket_url: str = "ws://localhost:8000/ws/realtime"):
        self.api_websocket_url = api_websocket_url
        self.websocket = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5
        
    async def connect(self):
        """Connect to the API WebSocket endpoint"""
        try:
            self.websocket = await websockets.connect(self.api_websocket_url)
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info(f"✅ Connected to WebSocket API at {self.api_websocket_url}")
            
            # Send initial ping
            await self.send_message({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to WebSocket API: {e}")
            self.is_connected = False
            await self._schedule_reconnect()
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.is_connected = False
            logger.info("🛑 Disconnected from WebSocket API")
    
    async def _schedule_reconnect(self):
        """Schedule a reconnection attempt"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self.max_reconnect_attempts}) reached")
            return
        
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * self.reconnect_attempts
        logger.info(f"📡 Scheduling reconnection attempt {self.reconnect_attempts} in {delay}s")
        
        await asyncio.sleep(delay)
        await self.connect()
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the WebSocket API"""
        if not self.is_connected or not self.websocket:
            logger.warning("WebSocket not connected, cannot send message")
            return False
        
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.is_connected = False
            await self._schedule_reconnect()
            return False
    
    # ============================
    # Broadcast Methods
    # ============================
    
    async def broadcast_page_scraped(self, url: str, title: str, threat_level: str, keywords: list):
        """Broadcast when a new page is scraped"""
        message = {
            "type": "page_scraped",
            "data": {
                "url": url,
                "title": title,
                "threat_level": threat_level,
                "keywords": keywords,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.send_message(message)
        logger.info(f"📡 Broadcasted: Page scraped - {url}")
    
    async def broadcast_alert_created(self, alert_data: Dict[str, Any]):
        """Broadcast when a new alert is created"""
        message = {
            "type": "new_alert",
            "data": {
                "url": alert_data.get("url"),
                "title": alert_data.get("title"),
                "threat_level": alert_data.get("threat_level"),
                "keywords_found": alert_data.get("keywords_found", []),
                "timestamp": alert_data.get("timestamp", datetime.now().isoformat())
            }
        }
        await self.send_message(message)
        logger.info(f"🚨 Broadcasted: New alert - {alert_data.get('threat_level')} threat")
    
    async def broadcast_ai_analysis_complete(self, analysis_data: Dict[str, Any]):
        """Broadcast when AI analysis is completed"""
        message = {
            "type": "ai_analysis_complete",
            "data": {
                "url": analysis_data.get("url"),
                "threat_level": analysis_data.get("threat_level"),
                "confidence_score": analysis_data.get("confidence_score"),
                "threat_categories": analysis_data.get("threat_categories", []),
                "illegal_content_detected": analysis_data.get("illegal_content_detected", False),
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.send_message(message)
        logger.info(f"🤖 Broadcasted: AI analysis complete - {analysis_data.get('threat_level')} threat")
    
    async def broadcast_crawler_stats(self, stats: Dict[str, Any]):
        """Broadcast updated crawler statistics"""
        message = {
            "type": "stats_update",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_message(message)
        logger.debug("📊 Broadcasted: Stats update")
    
    async def broadcast_link_discovered(self, source_url: str, target_url: str, link_count: int):
        """Broadcast when new links are discovered"""
        message = {
            "type": "links_discovered",
            "data": {
                "source_url": source_url,
                "target_url": target_url,
                "total_links": link_count,
                "timestamp": datetime.now().isoformat()
            }
        }
        await self.send_message(message)
        logger.debug(f"🔗 Broadcasted: Links discovered from {source_url}")

# ============================
# Synchronous Wrapper Functions
# ============================

# Global notifier instance
_notifier = None
_loop = None
_thread = None

def _run_event_loop():
    """Run the asyncio event loop in a separate thread"""
    global _loop
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop.run_forever()

def init_realtime_notifier():
    """Initialize the real-time notifier service"""
    global _notifier, _loop, _thread
    
    if _notifier is not None:
        return _notifier
    
    # Start event loop in separate thread
    _thread = threading.Thread(target=_run_event_loop, daemon=True)
    _thread.start()
    
    # Wait for loop to be ready
    time.sleep(0.1)
    
    # Create notifier instance
    _notifier = RealtimeNotifier()
    
    # Schedule connection
    if _loop:
        asyncio.run_coroutine_threadsafe(_notifier.connect(), _loop)
    
    return _notifier

def notify_page_scraped(url: str, title: str, threat_level: str = "LOW", keywords: list = None):
    """Synchronous wrapper for broadcasting page scraped"""
    global _notifier, _loop
    if _notifier and _loop:
        try:
            asyncio.run_coroutine_threadsafe(
                _notifier.broadcast_page_scraped(url, title, threat_level, keywords or []), 
                _loop
            )
        except Exception as e:
            logger.error(f"Error notifying page scraped: {e}")

def notify_alert_created(alert_data: Dict[str, Any]):
    """Synchronous wrapper for broadcasting alert created"""
    global _notifier, _loop
    if _notifier and _loop:
        try:
            asyncio.run_coroutine_threadsafe(
                _notifier.broadcast_alert_created(alert_data), 
                _loop
            )
        except Exception as e:
            logger.error(f"Error notifying alert created: {e}")

def notify_ai_analysis_complete(analysis_data: Dict[str, Any]):
    """Synchronous wrapper for broadcasting AI analysis complete"""
    global _notifier, _loop
    if _notifier and _loop:
        try:
            asyncio.run_coroutine_threadsafe(
                _notifier.broadcast_ai_analysis_complete(analysis_data), 
                _loop
            )
        except Exception as e:
            logger.error(f"Error notifying AI analysis complete: {e}")

def notify_links_discovered(source_url: str, target_url: str, link_count: int):
    """Synchronous wrapper for broadcasting links discovered"""
    global _notifier, _loop
    if _notifier and _loop:
        try:
            asyncio.run_coroutine_threadsafe(
                _notifier.broadcast_link_discovered(source_url, target_url, link_count), 
                _loop
            )
        except Exception as e:
            logger.error(f"Error notifying links discovered: {e}")

def shutdown_realtime_notifier():
    """Shutdown the real-time notifier service"""
    global _notifier, _loop, _thread
    
    if _notifier and _loop:
        try:
            asyncio.run_coroutine_threadsafe(_notifier.disconnect(), _loop)
        except Exception as e:
            logger.error(f"Error disconnecting notifier: {e}")
    
    if _loop:
        _loop.call_soon_threadsafe(_loop.stop)
    
    _notifier = None
    _loop = None
    _thread = None

# Initialize on import
try:
    init_realtime_notifier()
    logger.info("🚀 Real-time notifier initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize real-time notifier: {e}")
