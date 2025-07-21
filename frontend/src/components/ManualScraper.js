import React, { useState } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import toast from 'react-hot-toast';

const ManualScraper = () => {
  const [torUrl, setTorUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanHistory, setScanHistory] = useState([]);

  const handleStartScan = async () => {
    if (!torUrl.trim()) {
      toast.error('⚠️ Please enter a valid TOR link');
      return;
    }

    setIsScanning(true);
    
    try {
      // Format URL if needed
      let formattedUrl = torUrl.trim();
      if (!formattedUrl.startsWith('http://') && !formattedUrl.startsWith('https://')) {
        formattedUrl = 'http://' + formattedUrl;
      }

      // Start the crawler via API
      const response = await axios.post('/api/crawler/start', {
        url: formattedUrl,
        scan_type: 'manual'
      });

      if (response.data.success) {
        toast.success('🟢 Scraper started successfully!');
        
        // Add to scan history
        const newScan = {
          id: Date.now(),
          url: formattedUrl,
          status: 'running',
          timestamp: new Date().toISOString(),
          process_id: response.data.process_id
        };
        
        setScanHistory(prev => [newScan, ...prev]);
        setTorUrl('');
      } else {
        toast.error('❌ Failed to start scraper: ' + response.data.message);
      }
    } catch (error) {
      console.error('Scan error:', error);
      toast.error('❌ Failed to start scraper: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsScanning(false);
    }
  };

  const handleStopScan = async (scanId, processId) => {
    try {
      await axios.post('/api/crawler/stop', { process_id: processId });
      
      setScanHistory(prev => 
        prev.map(scan => 
          scan.id === scanId 
            ? { ...scan, status: 'stopped' }
            : scan
        )
      );
      
      toast.success('🛑 Scan stopped');
    } catch (error) {
      toast.error('❌ Failed to stop scan');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return '#22c55e';
      case 'completed': return '#3b82f6';
      case 'stopped': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <motion.div 
      className="manual-scraper"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="scraper-container">
        <motion.div 
          className="scraper-input-section"
          whileHover={{ scale: 1.02 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <h3 className="scraper-title">🧪 Manual TOR Scraper</h3>
          <p className="scraper-subtitle">Enter a .onion URL to start deep web intelligence gathering</p>
          
          <div className="input-group">
            <div className="input-container">
              <span className="input-icon">🔗</span>
              <input
                type="text"
                value={torUrl}
                onChange={(e) => setTorUrl(e.target.value)}
                placeholder="http://example.onion"
                className="tor-input"
                disabled={isScanning}
                onKeyPress={(e) => e.key === 'Enter' && handleStartScan()}
              />
            </div>
            
            <motion.button
              onClick={handleStartScan}
              disabled={isScanning || !torUrl.trim()}
              className={`scan-button ${isScanning ? 'scanning' : ''}`}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {isScanning ? (
                <>
                  <span className="spinner"></span>
                  🕷️ Scanning...
                </>
              ) : (
                '🕷️ Start Scraping'
              )}
            </motion.button>
          </div>
          
          <div className="scan-info">
            <div className="info-item">
              <span className="info-icon">⚡</span>
              <span>Real-time threat detection</span>
            </div>
            <div className="info-item">
              <span className="info-icon">🧠</span>
              <span>AI-powered content analysis</span>
            </div>
            <div className="info-item">
              <span className="info-icon">🔒</span>
              <span>Anonymous scanning via TOR</span>
            </div>
          </div>
        </motion.div>

        {/* Scan History */}
        {scanHistory.length > 0 && (
          <motion.div 
            className="scan-history"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            transition={{ delay: 0.3 }}
          >
            <h4 className="history-title">📊 Recent Scans</h4>
            
            <div className="history-list">
              {scanHistory.map((scan) => (
                <motion.div 
                  key={scan.id}
                  className="history-item"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 }}
                  whileHover={{ x: 5 }}
                >
                  <div className="scan-details">
                    <div className="scan-url">{scan.url}</div>
                    <div className="scan-time">
                      {new Date(scan.timestamp).toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="scan-status-container">
                    <div 
                      className="scan-status"
                      style={{ color: getStatusColor(scan.status) }}
                    >
                      {scan.status === 'running' && '🟢'}
                      {scan.status === 'completed' && '✅'}
                      {scan.status === 'stopped' && '🟡'}
                      {scan.status === 'error' && '🔴'}
                      {scan.status.toUpperCase()}
                    </div>
                    
                    {scan.status === 'running' && (
                      <motion.button
                        onClick={() => handleStopScan(scan.id, scan.process_id)}
                        className="stop-button"
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                      >
                        🛑
                      </motion.button>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default ManualScraper;
