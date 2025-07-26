import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

// Configure axios base URL for API calls
const API_BASE_URL = 'http://localhost:8000';
axios.defaults.baseURL = API_BASE_URL;

// MINIMAL Dashboard Component - NO API calls
const Dashboard = ({ dashboardData }) => {
  return (
    <motion.div 
      className="dashboard"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <h2>🏠 TRINETRA Dashboard</h2>
      <div className="dashboard-grid">
        <div className="stat-card">
          <div className="stat-title">Total URLs Crawled</div>
          <div className="stat-value">{dashboardData?.total_urls || 0}</div>
          <div className="stat-icon">🕸️</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-title">Active Alerts</div>
          <div className="stat-value">{dashboardData?.active_alerts || 0}</div>
          <div className="stat-icon">⚠️</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-title">AI Analyses</div>
          <div className="stat-value">{dashboardData?.ai_analyses || 0}</div>
          <div className="stat-icon">🧠</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-title">Threat Level</div>
          <div className="stat-value">{dashboardData?.threat_level || 'LOW'}</div>
          <div className="stat-icon">🚨</div>
        </div>
      </div>
      
      <div style={{ marginTop: '20px', padding: '20px', background: '#1a1a1a', borderRadius: '8px' }}>
        <h3>🚀 System Status: OPERATIONAL</h3>
        <p>Backend is running and responding to requests.</p>
        <p>Last updated: {new Date().toLocaleTimeString()}</p>
      </div>
    </motion.div>
  );
};

// MINIMAL placeholder components - NO API calls
const ManualScraper = () => (
  <div style={{ padding: '20px' }}>
    <h2>🧪 Manual Scraper</h2>
    <p>Manual scraper interface - Coming soon</p>
  </div>
);

const AlertBrowser = () => (
  <div style={{ padding: '20px' }}>
    <h2>⚠️ Alert Browser</h2>
    <p>Alert browser interface - Coming soon</p>
  </div>
);

const AIAnalysis = () => (
  <div style={{ padding: '20px' }}>
    <h2>🧠 AI Analysis</h2>
    <p>AI analysis interface - Coming soon</p>
  </div>
);

const IncidentReporting = () => (
  <div style={{ padding: '20px' }}>
    <h2>🚨 Incident Reporting</h2>
    <p>Incident reporting interface - Coming soon</p>
  </div>
);

const ManualControl = () => (
  <div style={{ padding: '20px' }}>
    <h2>🔧 Manual Control</h2>
    <p>Manual control interface - Coming soon</p>
  </div>
);

const LiveMonitoring = () => (
  <div style={{ padding: '20px' }}>
    <h2>📡 Live Monitoring</h2>
    <p>Live monitoring interface - Coming soon</p>
  </div>
);

const TimelineAnalysis = () => (
  <div style={{ padding: '20px' }}>
    <h2>📊 Timeline Analysis</h2>
    <p>Timeline analysis interface - Coming soon</p>
  </div>
);

const KeywordAnalytics = () => (
  <div style={{ padding: '20px' }}>
    <h2>🔍 Keyword Analytics</h2>
    <p>Keyword analytics interface - Coming soon</p>
  </div>
);

const LinkMap = () => (
  <div style={{ padding: '20px' }}>
    <h2>🕸️ Link Map</h2>
    <p>Link map interface - Coming soon</p>
  </div>
);

// Navigation Component
const Navigation = ({ currentView, setCurrentView }) => {
  const navItems = [
    { id: 'dashboard', label: '🏠 Dashboard', icon: '🏠' },
    { id: 'scraper', label: '🧪 Manual Scraper', icon: '🧪' },
    { id: 'control', label: '🔧 Manual Control', icon: '🔧' },
    { id: 'incidents', label: '🚨 Incident Reports', icon: '🚨' },
    { id: 'linkmap', label: '🕸️ Link Map', icon: '🕸️' },
    { id: 'timeline', label: '📊 Timeline Analysis', icon: '📊' },
    { id: 'keywords', label: '🔍 Keyword Analytics', icon: '🔍' },
    { id: 'alerts', label: '⚠️ Alerts', icon: '⚠️' },
    { id: 'ai', label: '🧠 AI Analysis', icon: '🧠' },
    { id: 'monitor', label: '📡 Live Monitor', icon: '📡' }
  ];

  return (
    <nav className="navigation" style={{ width: '250px', background: '#0a1a0a', height: '100vh', padding: '20px' }}>
      <div className="nav-header">
        <h1 style={{ color: '#00ff88', textAlign: 'center', marginBottom: '30px' }}>TRINETRA</h1>
      </div>
      
      <div className="nav-items">
        {navItems.map((item) => (
          <div
            key={item.id}
            className={`nav-item ${currentView === item.id ? 'active' : ''}`}
            onClick={() => setCurrentView(item.id)}
            style={{
              padding: '12px',
              margin: '5px 0',
              background: currentView === item.id ? '#00ff88' : 'transparent',
              color: currentView === item.id ? '#000' : '#00ff88',
              cursor: 'pointer',
              borderRadius: '5px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}
          >
            <span>{item.icon}</span>
            <span>{item.label.split(' ').slice(1).join(' ')}</span>
          </div>
        ))}
      </div>
    </nav>
  );
};

// Status Display Component
const StatusDisplay = ({ backendHealth, lastUpdated }) => {
  return (
    <div style={{ 
      padding: '10px 20px', 
      background: '#1a1a1a', 
      borderBottom: '1px solid #333',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      <div>
        <span style={{ color: '#00ff88' }}>Backend: </span>
        <span style={{ color: backendHealth ? '#00ff88' : '#ff4444' }}>
          {backendHealth ? '🟢 ONLINE' : '🔴 OFFLINE'}
        </span>
      </div>
      <div style={{ color: '#888', fontSize: '12px' }}>
        Last updated: {lastUpdated}
      </div>
    </div>
  );
};

// MAIN APP COMPONENT - ULTRA MINIMAL API CALLS
const App = () => {
  const [currentView, setCurrentView] = useState('dashboard');
  const [backendHealth, setBackendHealth] = useState(false);
  const [dashboardData, setDashboardData] = useState({
    total_urls: 0,
    active_alerts: 0,
    ai_analyses: 0,
    threat_level: 'LOW'
  });
  const [lastUpdated, setLastUpdated] = useState('Never');

  // SINGLE useEffect - NO frequent calls
  useEffect(() => {
    const initializeApp = async () => {
      console.log('🚀 Initializing TRINETRA app...');
      
      try {
        // Single health check on startup
        const healthResponse = await axios.get('/api/health');
        setBackendHealth(healthResponse.status === 200);
        console.log('✅ Backend health check passed');
        
        // Single dashboard data fetch on startup
        const dashboardResponse = await axios.get('/api/dashboard');
        setDashboardData(dashboardResponse.data);
        console.log('✅ Dashboard data loaded');
        
        setLastUpdated(new Date().toLocaleTimeString());
        
      } catch (error) {
        console.error('❌ App initialization failed:', error);
        setBackendHealth(false);
      }
    };

    // Initialize once
    initializeApp();

    // ONLY ONE interval - very infrequent updates
    const healthInterval = setInterval(async () => {
      try {
        const response = await axios.get('/api/health');
        setBackendHealth(response.status === 200);
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (error) {
        setBackendHealth(false);
        setLastUpdated('Error: ' + new Date().toLocaleTimeString());
      }
    }, 60000); // Only every 60 seconds

    // Cleanup
    return () => {
      clearInterval(healthInterval);
    };
  }, []); // NO dependencies to prevent re-runs

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard dashboardData={dashboardData} />;
      case 'scraper':
        return <ManualScraper />;
      case 'control':
        return <ManualControl />;
      case 'incidents':
        return <IncidentReporting />;
      case 'linkmap':
        return <LinkMap />;
      case 'alerts':
        return <AlertBrowser />;
      case 'timeline':
        return <TimelineAnalysis />;
      case 'keywords':
        return <KeywordAnalytics />;
      case 'ai':
        return <AIAnalysis />;
      case 'monitor':
        return <LiveMonitoring />;
      default:
        return <Dashboard dashboardData={dashboardData} />;
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      minHeight: '100vh', 
      background: '#000', 
      color: '#00ff88',
      fontFamily: 'monospace'
    }}>
      <Navigation currentView={currentView} setCurrentView={setCurrentView} />
      
      <div style={{ flex: 1 }}>
        <StatusDisplay backendHealth={backendHealth} lastUpdated={lastUpdated} />
        
        <main style={{ padding: '20px', height: 'calc(100vh - 60px)', overflowY: 'auto' }}>
          {renderCurrentView()}
        </main>
      </div>
    </div>
  );
};

export default App;
