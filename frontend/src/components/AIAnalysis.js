import React, { useState, useEffect } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
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
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const AIAnalysis = () => {
  const [aiData, setAiData] = useState(null);
  const [aiStats, setAiStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [threatLevelFilter, setThreatLevelFilter] = useState('all');

  useEffect(() => {
    fetchAIData();
    fetchAIStats();
  }, [threatLevelFilter]);

  const fetchAIData = async () => {
    try {
      setLoading(true);
      const threatParam = threatLevelFilter !== 'all' ? `&threat_level=${threatLevelFilter}` : '';
      const response = await fetch(`http://localhost:8000/api/ai/analyses?limit=500${threatParam}`);
      const result = await response.json();

      if (result.success) {
        setAiData(result.data);
      } else {
        setError('Failed to load AI analyses');
      }
    } catch (err) {
      setError(`Error fetching AI analyses: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchAIStats = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/ai/statistics`);
      const result = await response.json();

      if (result.success) {
        setAiStats(result.data);
      }
    } catch (err) {
      console.error('Error fetching AI statistics:', err);
    }
  };

  const testAIConnection = async () => {
    try {
      setTestingConnection(true);
      const response = await fetch(`http://localhost:8000/api/ai/test-connection`, {
        method: 'POST',
      });
      const result = await response.json();
      setConnectionStatus(result);
    } catch (err) {
      setConnectionStatus({
        success: false,
        message: `Connection test failed: ${err.message}`
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const getThreatLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'critical': return '#ff4444';
      case 'high': return '#ff8844';
      case 'medium': return '#ffaa44';
      case 'low': return '#44aa44';
      default: return '#666666';
    }
  };

  const prepareConfidenceChart = () => {
    if (!aiData || aiData.length === 0) return null;

    const sortedData = [...aiData].sort((a, b) => 
      new Date(a.processed_at) - new Date(b.processed_at)
    );

    return {
      labels: sortedData.map((item, index) => `Analysis ${index + 1}`),
      datasets: [
        {
          label: 'Confidence Score',
          data: sortedData.map(item => (item.confidence_score * 100).toFixed(1)),
          borderColor: '#00d4aa',
          backgroundColor: 'rgba(0, 212, 170, 0.1)',
          borderWidth: 2,
          fill: true,
        },
      ],
    };
  };

  const prepareThreatDistribution = () => {
    if (!aiData || aiData.length === 0) return null;

    const threatCounts = {};
    aiData.forEach(item => {
      const level = item.threat_level || 'LOW';
      threatCounts[level] = (threatCounts[level] || 0) + 1;
    });

    const labels = Object.keys(threatCounts);
    const data = Object.values(threatCounts);

    return {
      labels,
      datasets: [{
        data,
        backgroundColor: labels.map(getThreatLevelColor),
        borderColor: labels.map(label => getThreatLevelColor(label) + 'dd'),
        borderWidth: 2,
      }],
    };
  };

  const prepareIllegalContentChart = () => {
    if (!aiData || aiData.length === 0) return null;

    const illegalCount = aiData.filter(item => item.illegal_content_detected).length;
    const legalCount = aiData.length - illegalCount;

    return {
      labels: ['Legal Content', 'Illegal Content Detected'],
      datasets: [{
        data: [legalCount, illegalCount],
        backgroundColor: ['#44aa44', '#ff4444'],
        borderColor: ['#44aa44dd', '#ff4444dd'],
        borderWidth: 2,
      }],
    };
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
  };

  const doughnutOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: '#00d4aa',
          usePointStyle: true,
        },
      },
    },
  };

  if (loading) {
    return (
      <div className="ai-analysis">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading AI analysis data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ai-analysis">
        <div className="error-container">
          <h3>⚠️ Error Loading AI Analysis</h3>
          <p>{error}</p>
          <button onClick={fetchAIData} className="retry-btn">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  const confidenceData = prepareConfidenceChart();
  const threatData = prepareThreatDistribution();
  const illegalData = prepareIllegalContentChart();

  return (
    <div className="ai-analysis">
      <div className="ai-header">
        <h2>🤖 AI Analysis Dashboard</h2>
        <div className="ai-controls">
          <div className="filter-section">
            <label>Filter by Threat Level:</label>
            <select 
              value={threatLevelFilter} 
              onChange={(e) => setThreatLevelFilter(e.target.value)}
              className="threat-filter"
            >
              <option value="all">All Levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
          <button 
            onClick={testAIConnection} 
            disabled={testingConnection}
            className="test-connection-btn"
          >
            {testingConnection ? '⏳ Testing...' : '🔗 Test AI Connection'}
          </button>
        </div>
      </div>

      {connectionStatus && (
        <div className={`connection-status ${connectionStatus.success ? 'success' : 'error'}`}>
          <h4>{connectionStatus.success ? '✅' : '❌'} AI Connection Status</h4>
          <p>{connectionStatus.message}</p>
          {connectionStatus.test_result && (
            <div className="test-result">
              <p><strong>Test Result:</strong></p>
              <p>Threat Level: <span className={`threat-badge ${connectionStatus.test_result.threat_level?.toLowerCase()}`}>
                {connectionStatus.test_result.threat_level}
              </span></p>
              <p>Confidence: {(connectionStatus.test_result.confidence_score * 100).toFixed(1)}%</p>
            </div>
          )}
        </div>
      )}

      {aiStats && (
        <div className="ai-stats-overview">
          <div className="stat-card">
            <span className="stat-value">{aiStats.total_ai_analyses || 0}</span>
            <span className="stat-label">Total Analyses</span>
          </div>
          <div className="stat-card illegal">
            <span className="stat-value">{aiStats.illegal_content_detected || 0}</span>
            <span className="stat-label">Illegal Content Detected</span>
          </div>
          <div className="stat-card confidence">
            <span className="stat-value">{((aiStats.avg_confidence_score || 0) * 100).toFixed(1)}%</span>
            <span className="stat-label">Avg Confidence</span>
          </div>
          <div className="stat-card signatures">
            <span className="stat-value">{aiStats.active_threat_signatures || 0}</span>
            <span className="stat-label">Active Signatures</span>
          </div>
        </div>
      )}

      <div className="ai-charts">
        <div className="chart-container large">
          <h3>Confidence Score Trends</h3>
          {confidenceData && <Line data={confidenceData} options={chartOptions} />}
        </div>

        <div className="chart-row">
          <div className="chart-container medium">
            <h3>Threat Level Distribution</h3>
            {threatData && <Doughnut data={threatData} options={doughnutOptions} />}
          </div>
          <div className="chart-container medium">
            <h3>Content Classification</h3>
            {illegalData && <Doughnut data={illegalData} options={doughnutOptions} />}
          </div>
        </div>
      </div>

      <div className="analysis-table">
        <h3>Recent AI Analyses</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>URL</th>
                <th>Threat Level</th>
                <th>Confidence</th>
                <th>Illegal Content</th>
                <th>Categories</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {aiData && aiData.slice(0, 20).map((analysis, index) => (
                <tr key={index}>
                  <td className="date-cell">
                    {new Date(analysis.processed_at).toLocaleDateString()}
                  </td>
                  <td className="url-cell">
                    {analysis.url?.length > 50 ? 
                      `${analysis.url.substring(0, 50)}...` : 
                      analysis.url}
                  </td>
                  <td className={`threat-cell ${analysis.threat_level?.toLowerCase()}`}>
                    {analysis.threat_level}
                  </td>
                  <td className="confidence-cell">
                    {(analysis.confidence_score * 100).toFixed(1)}%
                  </td>
                  <td className="illegal-cell">
                    {analysis.illegal_content_detected ? 
                      <span className="illegal-badge">⚠️ YES</span> : 
                      <span className="legal-badge">✅ NO</span>
                    }
                  </td>
                  <td className="categories-cell">
                    {analysis.threat_categories?.slice(0, 2).join(', ')}
                    {analysis.threat_categories?.length > 2 && '...'}
                  </td>
                  <td className="actions-cell">
                    <button 
                      onClick={() => setSelectedAnalysis(analysis)}
                      className="detail-btn"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedAnalysis && (
        <div className="analysis-detail-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>AI Analysis Details</h3>
              <button 
                onClick={() => setSelectedAnalysis(null)}
                className="close-btn"
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="analysis-info">
                <div className="info-row">
                  <strong>URL:</strong> {selectedAnalysis.url}
                </div>
                <div className="info-row">
                  <strong>Processed At:</strong> {new Date(selectedAnalysis.processed_at).toLocaleString()}
                </div>
                <div className="info-row">
                  <strong>Threat Level:</strong> 
                  <span className={`threat-badge ${selectedAnalysis.threat_level?.toLowerCase()}`}>
                    {selectedAnalysis.threat_level}
                  </span>
                </div>
                <div className="info-row">
                  <strong>Confidence Score:</strong> {(selectedAnalysis.confidence_score * 100).toFixed(1)}%
                </div>
                <div className="info-row">
                  <strong>Illegal Content:</strong> 
                  {selectedAnalysis.illegal_content_detected ? 
                    <span className="illegal-badge">⚠️ DETECTED</span> : 
                    <span className="legal-badge">✅ NOT DETECTED</span>
                  }
                </div>
              </div>

              {selectedAnalysis.threat_categories && selectedAnalysis.threat_categories.length > 0 && (
                <div className="threat-categories">
                  <h4>Threat Categories:</h4>
                  <div className="category-list">
                    {selectedAnalysis.threat_categories.map((category, index) => (
                      <span key={index} className="category-tag">
                        {category}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedAnalysis.suspicious_indicators && selectedAnalysis.suspicious_indicators.length > 0 && (
                <div className="suspicious-indicators">
                  <h4>Suspicious Indicators:</h4>
                  <div className="indicator-list">
                    {selectedAnalysis.suspicious_indicators.map((indicator, index) => (
                      <span key={index} className="indicator-tag">
                        {indicator}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {selectedAnalysis.analysis_summary && (
                <div className="analysis-summary">
                  <h4>AI Analysis Summary:</h4>
                  <p>{selectedAnalysis.analysis_summary}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="ai-controls-bottom">
        <button onClick={fetchAIData} className="refresh-btn">
          🔄 Refresh Data
        </button>
        <button onClick={() => window.location.href = '/manual-scraper'} className="new-analysis-btn">
          ➕ Start New Analysis
        </button>
      </div>
    </div>
  );
};

export default AIAnalysis;
