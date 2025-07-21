class WebSocketService {
  constructor() {
    this.ws = null;
    this.connectionCallbacks = [];
    this.statsUpdateCallbacks = [];
    this.crawlerEventCallbacks = [];
    this.alertReceivedCallbacks = [];
    this.analysisCompleteCallbacks = [];
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.reconnectInterval = 5000;
    this.reconnectTimeoutId = null;
    this.isConnecting = false;
    this.shouldReconnect = true;
    this.pingInterval = null;
    this.lastPingTime = null;
  }

  // Singleton pattern
  static getInstance() {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  connect(url = 'ws://localhost:8000/ws/realtime') {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      console.log('WebSocket already connecting or connected');
      return;
    }

    if (this.isConnecting) {
      console.log('WebSocket connection already in progress');
      return;
    }

    this.isConnecting = true;
    console.log(`Attempting to connect to WebSocket: ${url}`);

    try {
      this.ws = new WebSocket(url);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      this.isConnecting = false;
      this.notifyConnectionChange(false, error.message);
      this.scheduleReconnect();
    }
  }

  setupEventHandlers() {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected successfully');
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.notifyConnectionChange(true);
      
      // Start ping/pong mechanism
      this.startPing();
      
      // Send initial ping
      this.sendMessage({ type: 'ping' });
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error, event.data);
      }
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket connection closed:', event.code, event.reason);
      this.isConnecting = false;
      this.stopPing();
      
      // Only notify if we were previously connected
      if (this.reconnectAttempts === 0) {
        this.notifyConnectionChange(false);
      }
      
      // Schedule reconnect if enabled
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isConnecting = false;
      this.notifyConnectionChange(false, 'WebSocket connection error');
    };
  }

  handleMessage(data) {
    switch (data.type) {
      case 'pong':
        // Handle pong response for keep-alive
        this.lastPingTime = Date.now();
        break;

      case 'stats_update':
        this.notifyStatsUpdate(data.data);
        break;

      case 'crawler_started':
      case 'crawler_stopped':
      case 'crawler_error':
        this.notifyCrawlerEvent(data.type, data);
        break;

      case 'new_alert':
        this.notifyAlertReceived(data);
        break;

      case 'ai_analysis_complete':
        this.notifyAnalysisComplete(data);
        break;

      default:
        console.log('Unknown WebSocket message type:', data.type, data);
    }
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
      }
    } else {
      console.warn('Cannot send message: WebSocket not connected');
      return false;
    }
  }

  startPing() {
    // Send ping every 30 seconds to keep connection alive
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'ping' });
      }
    }, 30000);
  }

  stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  scheduleReconnect() {
    if (!this.shouldReconnect) return;
    
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached. Stopping reconnection.');
      this.notifyConnectionChange(false, 'Max reconnection attempts reached');
      return;
    }

    // Clear any existing timeout
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000); // Exponential backoff, max 30s
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts + 1} in ${delay}ms`);

    this.reconnectTimeoutId = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  disconnect() {
    console.log('Disconnecting WebSocket');
    this.shouldReconnect = false;
    
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
    
    this.stopPing();
    
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
  }

  forceReconnect() {
    console.log('Force reconnecting WebSocket');
    this.disconnect();
    this.shouldReconnect = true;
    this.reconnectAttempts = 0;
    setTimeout(() => {
      this.connect();
    }, 1000);
  }

  // Connection status methods
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  getConnectionState() {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'unknown';
    }
  }

  // Event subscription methods
  onConnectionChange(callback) {
    this.connectionCallbacks.push(callback);
    // Return unsubscribe function
    return () => {
      const index = this.connectionCallbacks.indexOf(callback);
      if (index > -1) {
        this.connectionCallbacks.splice(index, 1);
      }
    };
  }

  onStatsUpdate(callback) {
    this.statsUpdateCallbacks.push(callback);
    return () => {
      const index = this.statsUpdateCallbacks.indexOf(callback);
      if (index > -1) {
        this.statsUpdateCallbacks.splice(index, 1);
      }
    };
  }

  onCrawlerEvent(callback) {
    this.crawlerEventCallbacks.push(callback);
    return () => {
      const index = this.crawlerEventCallbacks.indexOf(callback);
      if (index > -1) {
        this.crawlerEventCallbacks.splice(index, 1);
      }
    };
  }

  onAlertReceived(callback) {
    this.alertReceivedCallbacks.push(callback);
    return () => {
      const index = this.alertReceivedCallbacks.indexOf(callback);
      if (index > -1) {
        this.alertReceivedCallbacks.splice(index, 1);
      }
    };
  }

  onAnalysisComplete(callback) {
    this.analysisCompleteCallbacks.push(callback);
    return () => {
      const index = this.analysisCompleteCallbacks.indexOf(callback);
      if (index > -1) {
        this.analysisCompleteCallbacks.splice(index, 1);
      }
    };
  }

  // Notification methods
  notifyConnectionChange(isConnected, error = null) {
    this.connectionCallbacks.forEach(callback => {
      try {
        callback(isConnected, error);
      } catch (err) {
        console.error('Error in connection change callback:', err);
      }
    });
  }

  notifyStatsUpdate(stats) {
    this.statsUpdateCallbacks.forEach(callback => {
      try {
        callback(stats);
      } catch (err) {
        console.error('Error in stats update callback:', err);
      }
    });
  }

  notifyCrawlerEvent(eventType, eventData) {
    this.crawlerEventCallbacks.forEach(callback => {
      try {
        callback(eventType, eventData);
      } catch (err) {
        console.error('Error in crawler event callback:', err);
      }
    });
  }

  notifyAlertReceived(alertData) {
    this.alertReceivedCallbacks.forEach(callback => {
      try {
        callback(alertData);
      } catch (err) {
        console.error('Error in alert received callback:', err);
      }
    });
  }

  notifyAnalysisComplete(analysisData) {
    this.analysisCompleteCallbacks.forEach(callback => {
      try {
        callback(analysisData);
      } catch (err) {
        console.error('Error in analysis complete callback:', err);
      }
    });
  }

  // Utility methods
  getConnectionInfo() {
    return {
      isConnected: this.isConnected(),
      state: this.getConnectionState(),
      reconnectAttempts: this.reconnectAttempts,
      shouldReconnect: this.shouldReconnect,
      lastPingTime: this.lastPingTime
    };
  }
}

export { WebSocketService };
