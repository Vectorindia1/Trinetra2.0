import React, { useState, useEffect } from 'react';
import { Bar, Pie, Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  Title,
  Tooltip,
  Legend
);

const KeywordAnalytics = () => {
  const [keywordData, setKeywordData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedKeyword, setSelectedKeyword] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchKeywordData();
  }, []);

  const fetchKeywordData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/keywords/analytics?limit=500`);
      const result = await response.json();

      if (result.success) {
        setKeywordData(result.data);
      } else {
        setError('Failed to load keyword analytics');
      }
    } catch (err) {
      setError(`Error fetching keyword analytics: ${err.message}`);
    } finally {
      setLoading(false);
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

  const prepareFrequencyChart = () => {
    if (!keywordData || !keywordData.keywords || keywordData.keywords.length === 0) return null;

    const topKeywords = keywordData.keywords.slice(0, 15);
    const keywords = topKeywords.map(item => item.keyword);
    const frequencies = topKeywords.map(item => item.frequency);
    const colors = topKeywords.map(item => getThreatLevelColor(item.avg_threat_level));

    return {
      labels: keywords,
      datasets: [
        {
          label: 'Frequency',
          data: frequencies,
          backgroundColor: colors,
          borderColor: colors.map(color => color + 'dd'),
          borderWidth: 2,
        },
      ],
    };
  };

  const prepareThreatDistribution = () => {
    if (!keywordData || !keywordData.keywords || keywordData.keywords.length === 0) return null;

    const threatLevels = {};
    keywordData.keywords.forEach(item => {
      const level = item.avg_threat_level || 'LOW';
      threatLevels[level] = (threatLevels[level] || 0) + item.frequency;
    });

    const labels = Object.keys(threatLevels);
    const data = Object.values(threatLevels);

    return {
      labels,
      datasets: [
        {
          data,
          backgroundColor: labels.map(getThreatLevelColor),
          borderColor: labels.map(label => getThreatLevelColor(label) + 'dd'),
          borderWidth: 2,
        },
      ],
    };
  };

  const prepareScatterChart = () => {
    if (!keywordData || !keywordData.keywords || keywordData.keywords.length === 0) return null;

    const data = keywordData.keywords.map(item => ({
      x: item.frequency,
      y: item.unique_urls,
      keyword: item.keyword,
      threat_level: item.avg_threat_level
    }));

    const criticalHigh = data.filter(d => ['CRITICAL', 'HIGH'].includes(d.threat_level));
    const mediumLow = data.filter(d => ['MEDIUM', 'LOW'].includes(d.threat_level));

    return {
      datasets: [
        {
          label: 'Critical/High Threat',
          data: criticalHigh,
          backgroundColor: '#ff4444',
          borderColor: '#ff4444dd',
          pointRadius: 6,
        },
        {
          label: 'Medium/Low Threat',
          data: mediumLow,
          backgroundColor: '#44aa44',
          borderColor: '#44aa44dd',
          pointRadius: 4,
        },
      ],
    };
  };

  const filteredKeywords = keywordData?.keywords?.filter(keyword => 
    keyword.keyword.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

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
          maxRotation: 45,
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

  const scatterOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#00d4aa',
        },
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const point = context.parsed;
            const keyword = context.raw.keyword;
            return `${keyword}: ${point.x} freq, ${point.y} URLs`;
          }
        }
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Frequency',
          color: '#00d4aa',
        },
        ticks: {
          color: '#00d4aa',
        },
        grid: {
          color: 'rgba(0, 212, 170, 0.1)',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Unique URLs',
          color: '#00d4aa',
        },
        ticks: {
          color: '#00d4aa',
        },
        grid: {
          color: 'rgba(0, 212, 170, 0.1)',
        },
      },
    },
  };

  const pieOptions = {
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
      <div className="keyword-analytics">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading keyword analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="keyword-analytics">
        <div className="error-container">
          <h3>⚠️ Error Loading Keyword Analytics</h3>
          <p>{error}</p>
          <button onClick={fetchKeywordData} className="retry-btn">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  const frequencyData = prepareFrequencyChart();
  const threatData = prepareThreatDistribution();
  const scatterData = prepareScatterChart();

  return (
    <div className="keyword-analytics">
      <div className="keyword-header">
        <h2>🔍 Keyword Analytics</h2>
        <div className="keyword-search">
          <input
            type="text"
            placeholder="Search keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      {keywordData?.statistics && (
        <div className="keyword-stats">
          <div className="stat-card">
            <span className="stat-value">{keywordData.statistics.total_keywords}</span>
            <span className="stat-label">Total Keywords</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{keywordData.statistics.threat_categories_count}</span>
            <span className="stat-label">Threat Categories</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{keywordData.statistics.suspicious_indicators_count}</span>
            <span className="stat-label">Suspicious Indicators</span>
          </div>
        </div>
      )}

      <div className="keyword-charts">
        <div className="chart-container large">
          <h3>Top Keywords by Frequency</h3>
          {frequencyData && <Bar data={frequencyData} options={chartOptions} />}
        </div>

        <div className="chart-row">
          <div className="chart-container medium">
            <h3>Threat Level Distribution</h3>
            {threatData && <Pie data={threatData} options={pieOptions} />}
          </div>
          <div className="chart-container medium">
            <h3>Frequency vs. URL Spread</h3>
            {scatterData && <Scatter data={scatterData} options={scatterOptions} />}
          </div>
        </div>
      </div>

      <div className="keyword-table">
        <h3>Keyword Details</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Keyword</th>
                <th>Frequency</th>
                <th>Threat Level</th>
                <th>Unique URLs</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredKeywords.slice(0, 20).map((keyword, index) => (
                <tr key={index}>
                  <td className="keyword-cell">{keyword.keyword}</td>
                  <td className="frequency-cell">{keyword.frequency}</td>
                  <td className={`threat-cell ${keyword.avg_threat_level?.toLowerCase()}`}>
                    {keyword.avg_threat_level}
                  </td>
                  <td className="url-count-cell">{keyword.unique_urls}</td>
                  <td className="actions-cell">
                    <button 
                      onClick={() => setSelectedKeyword(keyword)}
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

      {selectedKeyword && (
        <div className="keyword-detail-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Keyword Details: {selectedKeyword.keyword}</h3>
              <button 
                onClick={() => setSelectedKeyword(null)}
                className="close-btn"
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="keyword-info">
                <p><strong>Frequency:</strong> {selectedKeyword.frequency}</p>
                <p><strong>Threat Level:</strong> 
                  <span className={`threat-badge ${selectedKeyword.avg_threat_level?.toLowerCase()}`}>
                    {selectedKeyword.avg_threat_level}
                  </span>
                </p>
                <p><strong>Unique URLs:</strong> {selectedKeyword.unique_urls}</p>
              </div>
              <div className="related-urls">
                <h4>Related URLs:</h4>
                <div className="url-list">
                  {selectedKeyword.urls?.slice(0, 10).map((url, index) => (
                    <div key={index} className="url-item">
                      {url}
                    </div>
                  ))}
                  {selectedKeyword.urls?.length > 10 && (
                    <div className="url-more">
                      +{selectedKeyword.urls.length - 10} more URLs...
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="keyword-controls">
        <button onClick={fetchKeywordData} className="refresh-btn">
          🔄 Refresh Data
        </button>
      </div>
    </div>
  );
};

export default KeywordAnalytics;

