import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import Plot from 'react-plotly.js';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { AppProvider, useAppContext } from './contexts/AppContext';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

// Loading Screen Component
const LoadingScreen = ({ isLoading }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (isLoading) {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            return 100;
          }
          return prev + 2;
        });
      }, 50);
      return () => clearInterval(interval);
    }
  }, [isLoading]);

  if (!isLoading) return null;

  return (
    <motion.div 
      className="loading-screen"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="loading-content">
        <motion.div
          className="loading-logo"
          animate={{ 
            textShadow: [
              '0 0 20px #00ff88',
              '0 0 40px #00ff88',
              '0 0 20px #00ff88'
            ]
          }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          🕵️ TRINETRA
        </motion.div>
        
        <div className="loading-text">DARK WEB INTELLIGENCE SYSTEM</div>
        
        <div className="progress-bar">
          <motion.div 
            className="progress-fill"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
        
        <div className="loading-status">
          {progress < 30 && "Initializing quantum encryption..."}
          {progress >= 30 && progress < 60 && "Connecting to dark web nodes..."}
          {progress >= 60 && progress < 90 && "Loading intelligence modules..."}
          {progress >= 90 && "System ready. Welcome to TRINETRA."}
        </div>
      </div>
      
      <div className="matrix-rain">
        {[...Array(20)].map((_, i) => (
          <div key={i} className="matrix-column" style={{ left: `${i * 5}%` }}>
            {[...Array(20)].map((_, j) => (
              <span key={j} className="matrix-char" style={{ animationDelay: `${Math.random() * 3}s` }}>
                {String.fromCharCode(0x30A0 + Math.random() * 96)}
              </span>
            ))}
          </div>
        ))}
      </div>
    </motion.div>
  );
};

// Dashboard Component
const Dashboard = ({ dashboardData }) => {
  return (
    <motion.div 
      className="dashboard"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="dashboard-grid">
        <motion.div 
          className="stat-card"
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="stat-title">Total URLs Crawled</div>
          <div className="stat-value">{dashboardData?.total_urls || 0}</div>
          <div className="stat-icon">🕸️</div>
        </motion.div>
        
        <motion.div 
          className="stat-card"
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="stat-title">Active Alerts</div>
          <div className="stat-value">{dashboardData?.active_alerts || 0}</div>
          <div className="stat-icon">⚠️</div>
        </motion.div>
        
        <motion.div 
          className="stat-card"
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="stat-title">AI Analyses</div>
          <div className="stat-value">{dashboardData?.ai_analyses || 0}</div>
          <div className="stat-icon">🧠</div>
        </motion.div>
        
        <motion.div 
          className="stat-card"
          whileHover={{ scale: 1.05 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="stat-title">Threat Level</div>
          <div className="stat-value">{dashboardData?.threat_level || 'LOW'}</div>
          <div className="stat-icon">🚨</div>
        </motion.div>
      </div>
    </motion.div>
  );
};

// Import components
import ManualScraper from './components/ManualScraper';
import AlertBrowser from './components/AlertBrowser';
import TimelineAnalysis from './components/TimelineAnalysis';
import KeywordAnalytics from './components/KeywordAnalytics';
import AIAnalysis from './components/AIAnalysis';
import LiveMonitoring from './components/LiveMonitoring';

// Navigation Component
const Navigation = ({ currentView, setCurrentView }) => {
  const navItems = [
    { id: 'dashboard', label: '🏠 Dashboard', icon: '🏠' },
    { id: 'scraper', label: '🧪 Manual Scraper', icon: '🧪' },
    { id: 'timeline', label: '📊 Timeline Analysis', icon: '📊' },
    { id: 'keywords', label: '🔍 Keyword Analytics', icon: '🔍' },
    { id: 'alerts', label: '⚠️ Alerts', icon: '⚠️' },
    { id: 'ai', label: '🧠 AI Analysis', icon: '🧠' },
    { id: 'monitor', label: '📡 Live Monitor', icon: '📡' }
  ];

  return (
    <motion.nav 
      className="navigation"
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <div className="nav-header">
        <motion.div
          className="nav-logo"
          animate={{ 
            textShadow: [
              '0 0 10px #00ff88',
              '0 0 20px #00ff88',
              '0 0 10px #00ff88'
            ]
          }}
          transition={{ duration: 3, repeat: Infinity }}
        >
          🕵️ TRINETRA
        </motion.div>
      </div>
      
      <div className="nav-items">
        {navItems.map((item) => (
          <motion.div
            key={item.id}
            className={`nav-item ${currentView === item.id ? 'active' : ''}`}
            onClick={() => setCurrentView(item.id)}
            whileHover={{ x: 10, backgroundColor: 'rgba(0, 255, 136, 0.1)' }}
            whileTap={{ scale: 0.95 }}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label.split(' ').slice(1).join(' ')}</span>
          </motion.div>
        ))}
      </div>
    </motion.nav>
  );
};

// Status Display Component
const StatusDisplay = ({ backendHealth, connectionStatus }) => {
  return (
    <motion.div 
      className="status-display"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
    >
      <div className="status-item">
        <span className="status-label">Backend:</span>
        <span className={`status-value ${backendHealth ? 'online' : 'offline'}`}>
          {backendHealth ? '🟢 ONLINE' : '🔴 OFFLINE'}
        </span>
      </div>
      <div className="status-item">
        <span className="status-label">Connection:</span>
        <span className={`status-value ${connectionStatus === 'connected' ? 'online' : 'offline'}`}>
          {connectionStatus === 'connected' ? '🟢 CONNECTED' : '🟡 CONNECTING'}
        </span>
      </div>
    </motion.div>
  );
};

// Main App Component
// App Content Component (wrapped by AppProvider)
const AppContent = () => {
  const { state, actions, dispatch } = useAppContext();
  const [currentView, setCurrentView] = useState('dashboard');

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get('/api/health');
        actions.setBackendHealth(response.status === 200);
        dispatch({
          type: 'SET_CONNECTION_STATUS',
          payload: {
            isConnected: true,
            connectionStatus: 'connected'
          }
        });
      } catch (error) {
        console.error('Backend health check failed:', error);
        actions.setBackendHealth(false);
        dispatch({
          type: 'SET_CONNECTION_STATUS',
          payload: {
            isConnected: false,
            connectionStatus: 'disconnected'
          }
        });
      }
    };

    const fetchDashboard = async () => {
      try {
        const response = await axios.get('/api/dashboard');
        actions.setDashboardData(response.data);
      } catch (error) {
        console.error('Dashboard data fetch failed:', error);
      }
    };

    const init = async () => {
      await checkHealth();
      await fetchDashboard();

      setTimeout(() => {
        dispatch({ type: 'SET_LOADING', payload: false });
      }, 3000);
    };

    init();
  }, [actions, dispatch]);

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard dashboardData={state.dashboardData} />;
      case 'scraper':
        return <ManualScraper />;
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
        return <Dashboard dashboardData={state.dashboardData} />;
    }
  };

  return (
    <div className="app">
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a1a1a',
            color: '#00ff88',
            border: '1px solid #00ff8830',
            fontSize: '14px',
            fontFamily: 'Rajdhani, monospace'
          },
          success: {
            iconTheme: {
              primary: '#00ff88',
              secondary: '#1a1a1a'
            }
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#1a1a1a'
            }
          }
        }}
      />
      
      <AnimatePresence>
        <LoadingScreen isLoading={state.isLoading} />
      </AnimatePresence>
      
      {!state.isLoading && (
        <motion.div 
          className="app-content"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <Navigation currentView={currentView} setCurrentView={setCurrentView} />
          
          <main className="main-content">
            <StatusDisplay 
              backendHealth={state.backendHealth}
              connectionStatus={state.connectionStatus}
            />
            
            <div className="view-container">
              {renderCurrentView()}
            </div>
          </main>
          
          {/* Background effects */}
          <div className="bg-effects">
            <div className="grid-pattern"></div>
            <div className="wave-animation"></div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

// Main App Component with Provider
const App = () => {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
};

export default App;
