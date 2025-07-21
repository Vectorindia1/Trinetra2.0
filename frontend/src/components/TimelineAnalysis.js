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

const TimelineAnalysis = () => {
  const [timelineData, setTimelineData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('24h');

  useEffect(() => {
    fetchTimelineData();
  }, [timeRange]);

  const fetchTimelineData = async () => {
    try {
      setLoading(true);
      const hoursBack = timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 720;
      const response = await fetch(`http://localhost:8000/api/timeline/data?hours_back=${hoursBack}&limit=1000`);
      const result = await response.json();
      
      if (result.success) {
        setTimelineData(result.data);
      } else {
        setError('Failed to load timeline data');
      }
    } catch (err) {
      setError(`Error fetching timeline data: ${err.message}`);
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

  const prepareChartData = () => {
    if (!timelineData || !timelineData.hourly_threat_counts) return null;

    const hourlyData = timelineData.hourly_threat_counts;
    const hours = [...new Set(hourlyData.map(item => item.hour))].sort();
    const threatLevels = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];

    const datasets = threatLevels.map(level => ({
      label: level,
      data: hours.map(hour => {
        const item = hourlyData.find(d => d.hour === hour && d.threat_level === level);
        return item ? item.count : 0;
      }),
      backgroundColor: getThreatLevelColor(level),
      borderColor: getThreatLevelColor(level),
      borderWidth: 2,
    }));

    return {
      labels: hours.map(hour => new Date(hour).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit',
        month: 'short',
        day: 'numeric'
      })),
      datasets,
    };
  };

  const prepareConfidenceData = () => {
    if (!timelineData || !timelineData.hourly_confidence) return null;

    const confidenceData = timelineData.hourly_confidence;
    const hours = confidenceData.map(item => item.hour).sort();

    return {
      labels: hours.map(hour => new Date(hour).toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      })),
      datasets: [
        {
          label: 'Average Confidence',
          data: confidenceData.map(item => item.avg_confidence * 100),
          borderColor: '#00d4aa',
          backgroundColor: 'rgba(0, 212, 170, 0.1)',
          borderWidth: 2,
          fill: true,
        },
        {
          label: 'Analysis Count',
          data: confidenceData.map(item => item.analysis_count),
          borderColor: '#ff6b35',
          backgroundColor: 'rgba(255, 107, 53, 0.1)',
          borderWidth: 2,
          yAxisID: 'y1',
        },
      ],
    };
  };

  const prepareThreatDistribution = () => {
    if (!timelineData?.metrics?.threat_level_distribution) return null;

    const distribution = timelineData.metrics.threat_level_distribution;
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);

    return {
      labels,
      datasets: [{
        data,
        backgroundColor: labels.map(getThreatLevelColor),
        borderColor: labels.map(getThreatLevelColor),
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
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        ticks: {
          color: '#ff6b35',
        },
        grid: {
          drawOnChartArea: false,
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
      <div className="timeline-analysis">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading timeline analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="timeline-analysis">
        <div className="error-container">
          <h3>⚠️ Error Loading Timeline Data</h3>
          <p>{error}</p>
          <button onClick={fetchTimelineData} className="retry-btn">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  const chartData = prepareChartData();
  const confidenceData = prepareConfidenceData();
  const distributionData = prepareThreatDistribution();

  return (
    <div className="timeline-analysis">
      <div className="timeline-header">
        <h2>📊 Timeline Analysis</h2>
        <div className="time-range-selector">
          <button 
            className={timeRange === '24h' ? 'active' : ''} 
            onClick={() => setTimeRange('24h')}
          >
            24 Hours
          </button>
          <button 
            className={timeRange === '7d' ? 'active' : ''} 
            onClick={() => setTimeRange('7d')}
          >
            7 Days
          </button>
          <button 
            className={timeRange === '30d' ? 'active' : ''} 
            onClick={() => setTimeRange('30d')}
          >
            30 Days
          </button>
        </div>
      </div>

      {timelineData?.metrics && (
        <div className="metrics-overview">
          <div className="metric-card">
            <span className="metric-value">{timelineData.metrics.total_analyses}</span>
            <span className="metric-label">Total Analyses</span>
          </div>
          <div className="metric-card threat">
            <span className="metric-value">{timelineData.metrics.critical_high_threats}</span>
            <span className="metric-label">Critical/High Threats</span>
          </div>
          <div className="metric-card illegal">
            <span className="metric-value">{timelineData.metrics.illegal_content_count}</span>
            <span className="metric-label">Illegal Content Detected</span>
          </div>
          <div className="metric-card confidence">
            <span className="metric-value">{(timelineData.metrics.avg_confidence * 100).toFixed(1)}%</span>
            <span className="metric-label">Avg Confidence</span>
          </div>
        </div>
      )}

      <div className="timeline-charts">
        <div className="chart-container large">
          <h3>Threat Level Timeline</h3>
          {chartData && <Bar data={chartData} options={chartOptions} />}
        </div>

        <div className="chart-row">
          <div className="chart-container medium">
            <h3>Confidence Trends</h3>
            {confidenceData && <Line data={confidenceData} options={chartOptions} />}
          </div>
          <div className="chart-container medium">
            <h3>Threat Distribution</h3>
            {distributionData && <Doughnut data={distributionData} options={doughnutOptions} />}
          </div>
        </div>
      </div>

      {timelineData?.timeline_data && timelineData.timeline_data.length > 0 && (
        <div className="timeline-events">
          <h3>Recent Events</h3>
          <div className="events-list">
            {timelineData.timeline_data.slice(0, 10).map((event, index) => (
              <div key={index} className={`event-item ${event.threat_level?.toLowerCase()}`}>
                <div className="event-time">
                  {new Date(event.timestamp).toLocaleString()}
                </div>
                <div className="event-details">
                  <div className="event-url">{event.url}</div>
                  <div className="event-meta">
                    <span className={`threat-level ${event.threat_level?.toLowerCase()}`}>
                      {event.threat_level}
                    </span>
                    <span className="confidence">
                      {(event.confidence * 100).toFixed(1)}% confidence
                    </span>
                    {event.illegal_content && (
                      <span className="illegal-flag">⚠️ ILLEGAL CONTENT</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="timeline-controls">
        <button onClick={fetchTimelineData} className="refresh-btn">
          🔄 Refresh Data
        </button>
      </div>
    </div>
  );
};

export default TimelineAnalysis;
