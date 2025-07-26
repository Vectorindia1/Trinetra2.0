import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { WebSocketService } from '../services/WebSocketService';
import toast from 'react-hot-toast';

// Define action types
export const ACTIONS = {
  // Connection status
  SET_CONNECTION_STATUS: 'SET_CONNECTION_STATUS',
  SET_BACKEND_HEALTH: 'SET_BACKEND_HEALTH',
  
  // Dashboard and stats
  SET_DASHBOARD_DATA: 'SET_DASHBOARD_DATA',
  SET_LIVE_STATS: 'SET_LIVE_STATS',
  
  // Scanners and crawlers
  ADD_SCAN_HISTORY: 'ADD_SCAN_HISTORY',
  UPDATE_SCAN_STATUS: 'UPDATE_SCAN_STATUS',
  SET_ACTIVE_CRAWLERS: 'SET_ACTIVE_CRAWLERS',
  ADD_ACTIVE_CRAWLER: 'ADD_ACTIVE_CRAWLER',
  REMOVE_ACTIVE_CRAWLER: 'REMOVE_ACTIVE_CRAWLER',
  
  // Events and alerts
  ADD_RECENT_EVENT: 'ADD_RECENT_EVENT',
  CLEAR_RECENT_EVENTS: 'CLEAR_RECENT_EVENTS',
  ADD_ALERT: 'ADD_ALERT',
  
  // Performance data
  UPDATE_PERFORMANCE_DATA: 'UPDATE_PERFORMANCE_DATA',
  
  // General
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR'
};

// Initial state
const initialState = {
  // Connection status
  isConnected: false,
  backendHealth: false,
  connectionStatus: 'connecting',
  connectionError: null,
  
  // Dashboard data
  dashboardData: null,
  liveStats: null,
  
  // Scanners and crawlers
  scanHistory: [],
  activeCrawlers: [],
  
  // Events and alerts
  recentEvents: [],
  alerts: [],
  
  // Performance data for charts
  performanceData: {
    labels: [],
    alertCounts: [],
    threatLevels: [],
    timestamps: []
  },
  
  // General app state
  isLoading: true,
  error: null
};

// Reducer function
const appReducer = (state, action) => {
  switch (action.type) {
    case ACTIONS.SET_CONNECTION_STATUS:
      return {
        ...state,
        isConnected: action.payload.isConnected,
        connectionStatus: action.payload.connectionStatus,
        connectionError: action.payload.connectionError || null
      };
      
    case ACTIONS.SET_BACKEND_HEALTH:
      return {
        ...state,
        backendHealth: action.payload
      };
      
    case ACTIONS.SET_DASHBOARD_DATA:
      return {
        ...state,
        dashboardData: action.payload
      };
      
    case ACTIONS.SET_LIVE_STATS:
      return {
        ...state,
        liveStats: action.payload
      };
      
    case ACTIONS.ADD_SCAN_HISTORY:
      return {
        ...state,
        scanHistory: [action.payload, ...state.scanHistory.slice(0, 49)] // Keep last 50
      };
      
    case ACTIONS.UPDATE_SCAN_STATUS:
      return {
        ...state,
        scanHistory: state.scanHistory.map(scan =>
          scan.id === action.payload.id
            ? { ...scan, status: action.payload.status }
            : scan
        )
      };
      
    case ACTIONS.SET_ACTIVE_CRAWLERS:
      return {
        ...state,
        activeCrawlers: action.payload
      };
      
    case ACTIONS.ADD_ACTIVE_CRAWLER:
      return {
        ...state,
        activeCrawlers: [...state.activeCrawlers, action.payload]
      };
      
    case ACTIONS.REMOVE_ACTIVE_CRAWLER:
      return {
        ...state,
        activeCrawlers: state.activeCrawlers.filter(
          crawler => crawler.pid !== action.payload
        )
      };
      
    case ACTIONS.ADD_RECENT_EVENT:
      return {
        ...state,
        recentEvents: [action.payload, ...state.recentEvents.slice(0, 49)] // Keep last 50
      };
      
    case ACTIONS.CLEAR_RECENT_EVENTS:
      return {
        ...state,
        recentEvents: []
      };
      
    case ACTIONS.ADD_ALERT:
      return {
        ...state,
        alerts: [action.payload, ...state.alerts]
      };
      
    case ACTIONS.UPDATE_PERFORMANCE_DATA:
      const maxDataPoints = 20;
      const newPerfData = {
        labels: [...state.performanceData.labels, action.payload.timestamp].slice(-maxDataPoints),
        alertCounts: [...state.performanceData.alertCounts, action.payload.alertCount].slice(-maxDataPoints),
        threatLevels: [...state.performanceData.threatLevels, action.payload.threatLevel].slice(-maxDataPoints),
        timestamps: [...state.performanceData.timestamps, new Date()].slice(-maxDataPoints)
      };
      
      return {
        ...state,
        performanceData: newPerfData
      };
      
    case ACTIONS.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload
      };
      
    case ACTIONS.SET_ERROR:
      return {
        ...state,
        error: action.payload
      };
      
    default:
      return state;
  }
};

// Create context
const AppContext = createContext();

// Custom hook to use the context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

// Context provider component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // WebSocket disabled to prevent excessive API calls - can be re-enabled later
  useEffect(() => {
    console.log('🔌 WebSocket connections disabled for performance optimization');
    
    // Set initial connection status
    dispatch({
      type: ACTIONS.SET_CONNECTION_STATUS,
      payload: {
        isConnected: true,
        connectionStatus: 'connected',
        connectionError: null
      }
    });
    
    // No WebSocket initialization - prevents constant reconnection attempts
    // Can be re-enabled by uncommenting the WebSocket code when needed
  }, []);

  // Helper function
  const getCriticalHighCount = (stats) => {
    if (!stats.threat_levels?.alerts) return 0;
    const critical = stats.threat_levels.alerts.CRITICAL || 0;
    const high = stats.threat_levels.alerts.HIGH || 0;
    return critical + high;
  };

  // Action creators
  const actions = {
    setBackendHealth: (health) => 
      dispatch({ type: ACTIONS.SET_BACKEND_HEALTH, payload: health }),
      
    setDashboardData: (data) => 
      dispatch({ type: ACTIONS.SET_DASHBOARD_DATA, payload: data }),
      
    addScanHistory: (scan) => 
      dispatch({ type: ACTIONS.ADD_SCAN_HISTORY, payload: scan }),
      
    updateScanStatus: (id, status) => 
      dispatch({ type: ACTIONS.UPDATE_SCAN_STATUS, payload: { id, status } }),
      
    clearRecentEvents: () => 
      dispatch({ type: ACTIONS.CLEAR_RECENT_EVENTS }),
      
    setLoading: (loading) => 
      dispatch({ type: ACTIONS.SET_LOADING, payload: loading }),
      
    setError: (error) => 
      dispatch({ type: ACTIONS.SET_ERROR, payload: error })
  };

  const value = {
    state,
    actions,
    dispatch
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

export default AppContext;
