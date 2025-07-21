import React, { useState, useEffect, useRef } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const LiveMonitoring = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [liveStats, setLiveStats] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [activeCrawlers, setActiveCrawlers] = useState([]);
  const [performanceData, setPerformanceData] = useState({
    labels: [],
    alertCounts: [],
    threatLevels: [],
    timestamps: []
  });
  const [connectionError, setConnectionError] = useState(null);
  
  const websocketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const maxEvents = 50;
  const maxDataPoints = 20;

  useEffect(() => {
    connectWebSocket();
    return () => {
      disconnectWebSocket();
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const ws = new WebSocket('ws://localhost:8000/ws/realtime');
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        
        // Send initial ping
        ws.send(JSON.stringify({ type: 'ping' }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionError('WebSocket connection error');
        setIsConnected(false);
      };

    } catch (err) {
      console.error('Error creating WebSocket connection:', err);
      setConnectionError('Failed to create WebSocket connection');
      setIsConnected(false);
    }
  };

  const disconnectWebSocket = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
  };

  const handleWebSocketMessage = (data) => {
    const timestamp = new Date().toLocaleTimeString();

    switch (data.type) {
      case 'stats_update':
        setLiveStats(data.data);
        updatePerformanceData(data.data, timestamp);
        break;

      case 'crawler_started':
        const crawlerStartEvent = {
          type: 'crawler_started',
          message: `Crawler started for: ${data.url}`,
          timestamp: data.timestamp,
          url: data.url,
          pid: data.pid
        };
        addRecentEvent(crawlerStartEvent);
        updateActiveCrawlers(data.pid, data.url, 'started');
        break;

      case 'crawler_stopped':
        const crawlerStopEvent = {
          type: 'crawler_stopped',
          message: `Crawler stopped (PID: ${data.pid})`,
          timestamp: data.timestamp,
          pid: data.pid
        };
        addRecentEvent(crawlerStopEvent);
        updateActiveCrawlers(data.pid, null, 'stopped');
        break;

      case 'crawler_error':
        const errorEvent = {
          type: 'crawler_error',
          message: `Crawler error: ${data.error}`,
          timestamp: data.timestamp,
          error: data.error
        };
        addRecentEvent(errorEvent);
        break;

      case 'new_alert':
        const alertEvent = {
          type: 'new_alert',
          message: `New ${data.threat_level} alert detected`,
          timestamp: data.timestamp,
          threat_level: data.threat_level,
          url: data.url
        };
        addRecentEvent(alertEvent);
        break;

      case 'ai_analysis_complete':
        const analysisEvent = {
          type: 'ai_analysis_complete',
          message: `AI analysis completed: ${data.threat_level} threat`,
          timestamp: data.timestamp,
          threat_level: data.threat_level,
          confidence: data.confidence_score
        };
        addRecentEvent(analysisEvent);
        break;

      case 'pong':
        // Handle pong response
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const addRecentEvent = (event) => {
    setRecentEvents(prevEvents => {
      const newEvents = [event, ...prevEvents].slice(0, maxEvents);
      return newEvents;
    });
  };

  const updateActiveCrawlers = (pid, url, action) => {
    setActiveCrawlers(prevCrawlers => {
      if (action === 'started') {
        return [...prevCrawlers, { pid, url, startTime: new Date() }];
      } else if (action === 'stopped') {
        return prevCrawlers.filter(crawler => crawler.pid !== pid);
      }
      return prevCrawlers;
    });
  };

  const updatePerformanceData = (stats, timestamp) => {
    setPerformanceData(prevData => {
      const newLabels = [...prevData.labels, timestamp].slice(-maxDataPoints);
      const newAlertCounts = [...prevData.alertCounts, stats.overview?.total_alerts || 0].slice(-maxDataPoints);
      const newThreatLevels = [...prevData.threatLevels, getCriticalHighCount(stats)].slice(-maxDataPoints);
      const newTimestamps = [...prevData.timestamps, new Date()].slice(-maxDataPoints);

      return {
        labels: newLabels,
        alertCounts: newAlertCounts,
        threatLevels: newThreatLevels,
        timestamps: newTimestamps
      };
    });
  };

  const getCriticalHighCount = (stats) => {
    if (!stats.threat_levels?.alerts) return 0;
    const critical = stats.threat_levels.alerts.CRITICAL || 0;
    const high = stats.threat_levels.alerts.HIGH || 0;
    return critical + high;
  };

  const preparePerformanceChart = () => {
    return {
      labels: performanceData.labels,
      datasets: [
        {
          label: 'Total Alerts',
          data: performanceData.alertCounts,
          borderColor: '#00d4aa',
          backgroundColor: 'rgba(0, 212, 170, 0.1)',
          borderWidth: 2,
          fill: true,
        },
        {
          label: 'Critical/High Threats',
          data: performanceData.threatLevels,
          borderColor: '#ff4444',
          backgroundColor: 'rgba(255, 68, 68, 0.1)',
          borderWidth: 2,
          fill: true,
        },
      ],
    };
  };

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'crawler_started': return '🚀';
      case 'crawler_stopped': return '🛑';
      case 'crawler_error': return '❌';
      case 'new_alert': return '⚠️';
      case 'ai_analysis_complete': return '🤖';
      default: return '📡';
    }
  };

  const getEventClass = (event) => {
    switch (event.type) {
      case 'crawler_started': return 'success';
      case 'crawler_stopped': return 'info';
      case 'crawler_error': return 'error';
      case 'new_alert': 
        return event.threat_level?.toLowerCase() === 'critical' || event.threat_level?.toLowerCase() === 'high' 
          ? 'error' : 'warning';
      case 'ai_analysis_complete':
        return event.threat_level?.toLowerCase() === 'critical' || event.threat_level?.toLowerCase() === 'high'
          ? 'error' : 'success';
      default: return 'info';
    }
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#00d4aa',
        },
      },
      title: {
        display: false,
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#00d4aa',
        },
        grid: {
          color: 'rgba(0, 212, 170, 0.1)',
        },
      },
      y: {
        ticks: {
          color: '#00d4aa',
        },
        grid: {
          color: 'rgba(0, 212, 170, 0.1)',
        },
      },
    },
    animation: {
      duration: 0, // Disable animations for real-time data
    },
  };

  const performanceChart = preparePerformanceChart();

  return (
    <div className="live-monitoring">
      <div className="monitoring-header">
        <h2>📡 Live Monitoring</h2>
        <div className="connection-status">
          <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className={`status-dot ${isConnected ? 'success' : 'error'}`}></span>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
          {!isConnected && (
            <button onClick={connectWebSocket} className="reconnect-btn">
              🔄 Reconnect
            </button>
          )}
        </div>
      </div>

      {connectionError && (
        <div className="error-banner">
          <h4>⚠️ Connection Error</h4>
          <p>{connectionError}</p>
        </div>
      )}

      {liveStats && (
        <div className="live-stats-overview">
          <div className="stat-card">
            <span className="stat-value">{liveStats.overview?.total_alerts || 0}</span>
            <span className="stat-label">Total Alerts</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{liveStats.overview?.total_pages || 0}</span>
            <span className="stat-label">Pages Crawled</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{liveStats.overview?.total_ai_analyses || 0}</span>
            <span className="stat-label">AI Analyses</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{activeCrawlers.length}</span>
            <span className="stat-label">Active Crawlers</span>
          </div>
        </div>
      )}

      <div className="monitoring-content">
        <div className="performance-chart">
          <h3>Real-Time Performance</h3>
          <div className="chart-container">
            {performanceChart && <Line data={performanceChart} options={chartOptions} />}
          </div>
        </div>

        <div className="monitoring-panels">
          <div className="active-crawlers-panel">
            <h3>Active Crawlers ({activeCrawlers.length})</h3>
            <div className="crawlers-list">
              {activeCrawlers.length > 0 ? (
                activeCrawlers.map((crawler, index) => (
                  <div key={index} className="crawler-item">
                    <div className="crawler-info">
                      <div className="crawler-pid">PID: {crawler.pid}</div>
                      <div className="crawler-url">{crawler.url}</div>
                      <div className="crawler-time">
                        Started: {crawler.startTime.toLocaleTimeString()}
                      </div>
                    </div>
                    <div className="crawler-status">
                      <span className="status-dot success"></span>
                      Running
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-crawlers">
                  <p>No active crawlers</p>
                </div>
              )}
            </div>
          </div>

          <div className="live-events-panel">
            <h3>Live Events ({recentEvents.length})</h3>
            <div className="events-list">
              {recentEvents.length > 0 ? (
                recentEvents.map((event, index) => (
                  <div key={index} className={`event-item ${getEventClass(event)}`}>
                    <div className="event-icon">{getEventIcon(event.type)}</div>
                    <div className="event-content">
                      <div className="event-message">{event.message}</div>
                      <div className="event-timestamp">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </div>
                      {event.threat_level && (
                        <div className={`threat-badge ${event.threat_level.toLowerCase()}`}>
                          {event.threat_level}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-events">
                  <p>No recent events</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="monitoring-controls">
        <button 
          onClick={() => setRecentEvents([])} 
          className="clear-events-btn"
        >
          🗑️ Clear Events
        </button>
        <button 
          onClick={() => window.location.reload()} 
          className="refresh-monitoring-btn"
        >
          🔄 Refresh Monitoring
        </button>
      </div>
    </div>
  );
};

export default LiveMonitoring;
