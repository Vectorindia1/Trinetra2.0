import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import toast from 'react-hot-toast';

const AlertBrowser = () => {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    keyword: '',
    domain: '',
    severity: 'All',
    dateRange: 'all'
  });
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');

  useEffect(() => {
    fetchAlerts();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [alerts, filters, sortBy, sortOrder]);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/alerts');
      setAlerts(response.data.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      toast.error('❌ Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const getSeverity = (keywords) => {
    const highSeverity = ['bomb', 'terror', 'attack', 'kill', 'explosive', 'weapon', 'assassination', 'murder', 'violence'];
    const mediumSeverity = ['carding', 'hacking', 'drugs', 'malware', 'exploit', 'phishing', 'fraud', 'stealing', 'ransomware'];
    
    for (const keyword of keywords) {
      const keywordLower = keyword.toLowerCase();
      if (highSeverity.some(k => keywordLower.includes(k))) return 'High';
      if (mediumSeverity.some(k => keywordLower.includes(k))) return 'Medium';
    }
    return 'Low';
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'High': return '#ef4444';
      case 'Medium': return '#f59e0b';
      case 'Low': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const applyFilters = () => {
    let filtered = [...alerts];

    // Keyword filter
    if (filters.keyword) {
      filtered = filtered.filter(alert => 
        alert.keywords_found?.some(keyword => 
          keyword.toLowerCase().includes(filters.keyword.toLowerCase())
        )
      );
    }

    // Domain filter
    if (filters.domain) {
      filtered = filtered.filter(alert => 
        alert.url?.toLowerCase().includes(filters.domain.toLowerCase())
      );
    }

    // Severity filter
    if (filters.severity !== 'All') {
      filtered = filtered.filter(alert => 
        getSeverity(alert.keywords_found || []) === filters.severity
      );
    }

    // Date range filter
    if (filters.dateRange !== 'all') {
      const now = new Date();
      const filterDate = new Date();
      
      switch (filters.dateRange) {
        case '24h':
          filterDate.setHours(now.getHours() - 24);
          break;
        case '7d':
          filterDate.setDate(now.getDate() - 7);
          break;
        case '30d':
          filterDate.setDate(now.getDate() - 30);
          break;
        default:
          break;
      }
      
      filtered = filtered.filter(alert => 
        new Date(alert.timestamp) >= filterDate
      );
    }

    // Sort alerts
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortBy) {
        case 'timestamp':
          aValue = new Date(a.timestamp || 0);
          bValue = new Date(b.timestamp || 0);
          break;
        case 'severity':
          const severityOrder = { 'High': 3, 'Medium': 2, 'Low': 1 };
          aValue = severityOrder[getSeverity(a.keywords_found || [])];
          bValue = severityOrder[getSeverity(b.keywords_found || [])];
          break;
        case 'url':
          aValue = a.url || '';
          bValue = b.url || '';
          break;
        default:
          aValue = a[sortBy] || '';
          bValue = b[sortBy] || '';
      }

      if (sortOrder === 'desc') {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      } else {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      }
    });

    setFilteredAlerts(filtered);
  };

  const exportAlerts = () => {
    try {
      const csvContent = [
        ['Timestamp', 'URL', 'Title', 'Keywords', 'Severity'],
        ...filteredAlerts.map(alert => [
          alert.timestamp || 'N/A',
          alert.url || 'N/A',
          alert.title || 'N/A',
          (alert.keywords_found || []).join(', '),
          getSeverity(alert.keywords_found || [])
        ])
      ].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `threat_alerts_${new Date().toISOString().slice(0, 10)}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success('📥 Alerts exported successfully!');
    } catch (error) {
      toast.error('❌ Failed to export alerts');
    }
  };

  const AlertCard = ({ alert }) => {
    const severity = getSeverity(alert.keywords_found || []);
    const severityColor = getSeverityColor(severity);

    return (
      <motion.div 
        className="alert-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        whileHover={{ y: -2, boxShadow: `0 8px 30px ${severityColor}30` }}
        style={{ 
          borderLeft: `4px solid ${severityColor}`,
          backgroundColor: `${severityColor}10`
        }}
      >
        <div className="alert-header">
          <div className="alert-severity" style={{ color: severityColor }}>
            🚨 {severity.toUpperCase()} PRIORITY
          </div>
          <div className="alert-timestamp">
            📅 {new Date(alert.timestamp || Date.now()).toLocaleString()}
          </div>
        </div>

        <div className="alert-content">
          <div className="alert-field">
            <strong>🔗 URL:</strong>
            <a href={alert.url} target="_blank" rel="noopener noreferrer" className="alert-link">
              {alert.url || 'No URL'}
            </a>
          </div>

          <div className="alert-field">
            <strong>📖 Title:</strong>
            <span>{alert.title || 'No Title'}</span>
          </div>

          <div className="alert-field">
            <strong>🔍 Keywords:</strong>
            <div className="keywords-container">
              {(alert.keywords_found || []).map((keyword, index) => (
                <span key={index} className="keyword-tag" style={{ borderColor: severityColor }}>
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        </div>
      </motion.div>
    );
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner-large"></div>
        <p>Loading alerts...</p>
      </div>
    );
  }

  return (
    <motion.div 
      className="alert-browser"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <div className="browser-header">
        <h2>🔍 Advanced Alert Search & Filter</h2>
        <p>Search and analyze threat alerts with advanced filtering capabilities</p>
      </div>

      {/* Filter Controls */}
      <motion.div 
        className="filter-controls"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="filter-row">
          <div className="filter-group">
            <label>🔎 Filter by Keyword:</label>
            <input
              type="text"
              value={filters.keyword}
              onChange={(e) => setFilters(prev => ({ ...prev, keyword: e.target.value }))}
              placeholder="Enter keyword..."
              className="filter-input"
            />
          </div>

          <div className="filter-group">
            <label>🌐 Filter by Domain:</label>
            <input
              type="text"
              value={filters.domain}
              onChange={(e) => setFilters(prev => ({ ...prev, domain: e.target.value }))}
              placeholder="Enter domain..."
              className="filter-input"
            />
          </div>

          <div className="filter-group">
            <label>🚨 Severity:</label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
              className="filter-select"
            >
              <option value="All">All Severities</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div className="filter-group">
            <label>📅 Date Range:</label>
            <select
              value={filters.dateRange}
              onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
              className="filter-select"
            >
              <option value="all">All Time</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
            </select>
          </div>
        </div>

        <div className="sort-controls">
          <div className="sort-group">
            <label>📊 Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="sort-select"
            >
              <option value="timestamp">Timestamp</option>
              <option value="severity">Severity</option>
              <option value="url">URL</option>
            </select>
          </div>

          <div className="sort-group">
            <label>📈 Order:</label>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="sort-select"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
          </div>

          <motion.button
            onClick={exportAlerts}
            className="export-button"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={filteredAlerts.length === 0}
          >
            📥 Export CSV
          </motion.button>
        </div>
      </motion.div>

      {/* Results Summary */}
      <div className="results-summary">
        <p>Found <strong>{filteredAlerts.length}</strong> alerts matching your criteria</p>
      </div>

      {/* Alert List */}
      <div className="alerts-container">
        {filteredAlerts.length === 0 ? (
          <motion.div 
            className="no-alerts"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <h3>No alerts found</h3>
            <p>Try adjusting your filter criteria or check back later for new alerts.</p>
          </motion.div>
        ) : (
          <motion.div 
            className="alerts-list"
            layout
          >
            {filteredAlerts.slice(0, 50).map((alert, index) => (
              <AlertCard key={index} alert={alert} />
            ))}
            
            {filteredAlerts.length > 50 && (
              <div className="pagination-info">
                <p>Showing first 50 of {filteredAlerts.length} alerts. Refine your search for more specific results.</p>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default AlertBrowser;
