import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Plot from 'react-plotly.js';
import axios from 'axios';
import toast from 'react-hot-toast';
import './LinkMap.css';

const LinkMap = () => {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], stats: {} });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    nodeLimit: 500,
    threatLevels: ['MEDIUM', 'HIGH', 'CRITICAL'],
    layoutType: 'spring'
  });
  const [analytics, setAnalytics] = useState(null);

  const layoutOptions = [
    { value: 'spring', label: '🌸 Spring Layout' },
    { value: 'circular', label: '⭕ Circular Layout' },
    { value: 'kamada_kawai', label: '🎯 Force-Directed' },
    { value: 'spectral', label: '🌈 Spectral Layout' },
    { value: 'random', label: '🎲 Random Layout' }
  ];

  const threatLevelOptions = [
    { value: 'LOW', label: '🟢 Low', color: '#10b981' },
    { value: 'MEDIUM', label: '🟡 Medium', color: '#f59e0b' },
    { value: 'HIGH', label: '🔴 High', color: '#ef4444' },
    { value: 'CRITICAL', label: '🔴 Critical', color: '#dc2626' }
  ];

  useEffect(() => {
    fetchGraphData();
    fetchAnalytics();
  }, [filters]);

  const fetchGraphData = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/graph-data', {
        node_limit: filters.nodeLimit,
        threat_filter: filters.threatLevels.length > 0 ? filters.threatLevels : null,
        layout_type: filters.layoutType
      });
      
      setGraphData(response.data);
      
      if (response.data.nodes.length === 0) {
        toast('🔍 No graph data available. Start crawling to build the link map!', {
          icon: 'ℹ️'
        });
      }
    } catch (error) {
      console.error('Error fetching graph data:', error);
      toast.error('Failed to load graph data');
      setGraphData({ nodes: [], edges: [], stats: {} });
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get('/api/link-analytics');
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const createNetworkGraph = () => {
    if (!graphData.nodes || graphData.nodes.length === 0) {
      return {
        data: [],
        layout: {
          title: {
            text: '<b>🔍 No Network Data Available</b><br><sub>Start crawling to build connections</sub>',
            x: 0.5,
            font: { size: 18, color: '#64748b', family: 'Arial, sans-serif' }
          },
          plot_bgcolor: '#0f172a',
          paper_bgcolor: '#0f172a',
          showlegend: false,
          height: 700,
          xaxis: { showgrid: false, zeroline: false, showticklabels: false },
          yaxis: { showgrid: false, zeroline: false, showticklabels: false }
        }
      };
    }

    // Create node and edge data for Plotly
    const nodeMap = {};
    graphData.nodes.forEach((node, index) => {
      nodeMap[node.url] = { ...node, index };
    });

    // Position nodes in a spring-like layout (simplified)
    const positions = calculateNodePositions(graphData.nodes, graphData.edges);

    // Create edge traces with curves
    const edgeTraces = graphData.edges.map((edge, idx) => {
      const source = nodeMap[edge.source_url];
      const target = nodeMap[edge.target_url];
      
      if (!source || !target) return null;

      const sourcePos = positions[source.index];
      const targetPos = positions[target.index];
      
      if (!sourcePos || !targetPos) return null;

      // Calculate curved path
      const midX = (sourcePos.x + targetPos.x) / 2 + (Math.random() - 0.5) * 0.2;
      const midY = (sourcePos.y + targetPos.y) / 2 + (Math.random() - 0.5) * 0.2;
      
      // Edge thickness based on occurrence count
      const thickness = Math.min(Math.max((edge.occurrence_count || 1) * 0.5, 0.3), 3.0);
      
      // Edge color based on external/internal
      const edgeColor = edge.is_external ? 
        'rgba(99, 102, 241, 0.4)' : 'rgba(147, 51, 234, 0.6)';

      return {
        x: [sourcePos.x, midX, targetPos.x, null],
        y: [sourcePos.y, midY, targetPos.y, null],
        mode: 'lines',
        line: {
          width: thickness,
          color: edgeColor,
          shape: 'spline',
          smoothing: 1.0
        },
        hoverinfo: 'none',
        showlegend: false,
        opacity: 0.7,
        name: `Edge_${idx}`
      };
    }).filter(Boolean);

    // Create node trace
    const threatColors = {
      'LOW': '#10b981',
      'MEDIUM': '#f59e0b', 
      'HIGH': '#ef4444',
      'CRITICAL': '#dc2626'
    };

    const nodeTrace = {
      x: positions.map(pos => pos.x),
      y: positions.map(pos => pos.y),
      mode: 'markers+text',
      text: graphData.nodes.map(node => {
        const title = node.title || 'Untitled';
        if (title.length > 15) {
          if (node.url.includes('.onion')) {
            const domain = node.url.split('.onion')[0].split('//').pop();
            return domain.slice(0, 8).toUpperCase();
          }
          return title.slice(0, 12) + '...';
        }
        return title;
      }),
      textposition: 'middle center',
      textfont: {
        size: 9,
        color: 'white',
        family: 'Arial, sans-serif'
      },
      hoverinfo: 'text',
      hovertext: graphData.nodes.map(node => {
        const threatColor = threatColors[node.threat_level] || '#64748b';
        return `<b style='font-size:14px'>${node.title}</b><br>` +
               `<span style='font-family:monospace;font-size:11px'>${node.url.slice(0, 80)}...</span><br><br>` +
               `<b>🚨 Threat Level:</b> <span style='color:${threatColor}'>${node.threat_level}</span><br>` +
               `<b>🔗 Connections:</b> ${node.incoming_links || 0} in, ${node.outgoing_links || 0} out<br>` +
               `<b>📊 Centrality:</b> ${(node.centrality_score || 0).toFixed(3)}<br>` +
               `<b>📄 Page Size:</b> ${(node.page_size || 0).toLocaleString()} bytes<br>` +
               `<b>🕒 Last Crawled:</b> ${node.last_crawled || 'Never'}`;
      }),
      marker: {
        size: graphData.nodes.map(node => {
          const centrality = node.centrality_score || 0;
          const connections = (node.incoming_links || 0) + (node.outgoing_links || 0);
          const baseSize = 12;
          const centralityBonus = centrality * 8;
          const connectionBonus = connections * 0.5;
          return Math.min(Math.max(baseSize + centralityBonus + connectionBonus, 12), 35);
        }),
        color: graphData.nodes.map(node => 
          threatColors[node.threat_level] || '#64748b'
        ),
        line: {
          width: 2,
          color: 'rgba(255, 255, 255, 0.8)'
        },
        opacity: 0.9
      },
      name: 'Nodes',
      showlegend: false
    };

    return {
      data: [...edgeTraces, nodeTrace],
      layout: {
        title: {
          text: '<b>🕸️ Darknet Link Map</b><br><sub>Interactive Network Visualization</sub>',
          x: 0.5,
          font: { size: 22, color: '#e2e8f0', family: 'Arial, sans-serif' }
        },
        showlegend: false,
        hovermode: 'closest',
        margin: { b: 40, l: 40, r: 40, t: 80 },
        annotations: [
          {
            text: '<b>Legend:</b> Node size ∝ centrality • Color = threat level • Line thickness ∝ link frequency',
            showarrow: false,
            xref: 'paper', yref: 'paper',
            x: 0.5, y: -0.05,
            xanchor: 'center', yanchor: 'top',
            font: { size: 11, color: 'rgba(226, 232, 240, 0.8)' }
          },
          {
            text: '🟢 LOW | 🟡 MEDIUM | 🔴 HIGH | 🔴 CRITICAL',
            showarrow: false,
            xref: 'paper', yref: 'paper',
            x: 1.0, y: 1.0,
            xanchor: 'right', yanchor: 'top',
            font: { size: 10, color: 'rgba(226, 232, 240, 0.7)' }
          }
        ],
        xaxis: {
          showgrid: false,
          zeroline: false,
          showticklabels: false,
          range: [-2, 2]
        },
        yaxis: {
          showgrid: false,
          zeroline: false,
          showticklabels: false,
          range: [-2, 2]
        },
        plot_bgcolor: '#0f172a',
        paper_bgcolor: '#0f172a',
        font: { color: '#e2e8f0' },
        height: 750
      }
    };
  };

  const calculateNodePositions = (nodes, edges) => {
    // Simplified spring layout algorithm
    const positions = nodes.map((_, index) => ({
      x: (Math.random() - 0.5) * 4,
      y: (Math.random() - 0.5) * 4
    }));

    // Simple force simulation
    for (let iteration = 0; iteration < 50; iteration++) {
      const forces = positions.map(() => ({ x: 0, y: 0 }));
      
      // Repulsive forces between all nodes
      for (let i = 0; i < positions.length; i++) {
        for (let j = i + 1; j < positions.length; j++) {
          const dx = positions[i].x - positions[j].x;
          const dy = positions[i].y - positions[j].y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 0.1;
          const force = 0.1 / (distance * distance);
          
          forces[i].x += (dx / distance) * force;
          forces[i].y += (dy / distance) * force;
          forces[j].x -= (dx / distance) * force;
          forces[j].y -= (dy / distance) * force;
        }
      }
      
      // Attractive forces for connected nodes
      edges.forEach(edge => {
        const sourceIdx = nodes.findIndex(n => n.url === edge.source_url);
        const targetIdx = nodes.findIndex(n => n.url === edge.target_url);
        
        if (sourceIdx !== -1 && targetIdx !== -1) {
          const dx = positions[targetIdx].x - positions[sourceIdx].x;
          const dy = positions[targetIdx].y - positions[sourceIdx].y;
          const distance = Math.sqrt(dx * dx + dy * dy) || 0.1;
          const force = distance * 0.01;
          
          forces[sourceIdx].x += (dx / distance) * force;
          forces[sourceIdx].y += (dy / distance) * force;
          forces[targetIdx].x -= (dx / distance) * force;
          forces[targetIdx].y -= (dy / distance) * force;
        }
      });
      
      // Apply forces with damping
      for (let i = 0; i < positions.length; i++) {
        positions[i].x += forces[i].x * 0.1;
        positions[i].y += forces[i].y * 0.1;
      }
    }
    
    return positions;
  };

  const handleThreatFilterChange = (threat, checked) => {
    setFilters(prev => ({
      ...prev,
      threatLevels: checked 
        ? [...prev.threatLevels, threat]
        : prev.threatLevels.filter(t => t !== threat)
    }));
  };

  const refreshData = () => {
    toast.loading('Refreshing graph data...', { id: 'refresh' });
    fetchGraphData().then(() => {
      toast.success('Graph data refreshed!', { id: 'refresh' });
    });
  };

  const plotData = createNetworkGraph();

  return (
    <motion.div 
      className="link-map-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="link-map-header">
        <motion.h2 
          className="section-title"
          initial={{ x: -50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          🕸️ Link Map Explorer
        </motion.h2>
        <motion.p 
          className="section-subtitle"
          initial={{ x: -50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          Visualize the web of connections between discovered sites
        </motion.p>
      </div>

      {/* Control Panel */}
      <motion.div 
        className="control-panel"
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
      >
        <div className="control-group">
          <label>Max Nodes</label>
          <input
            type="range"
            min="50"
            max="2000"
            step="50"
            value={filters.nodeLimit}
            onChange={(e) => setFilters(prev => ({ ...prev, nodeLimit: parseInt(e.target.value) }))}
            className="range-slider"
          />
          <span className="range-value">{filters.nodeLimit}</span>
        </div>

        <div className="control-group">
          <label>Layout Algorithm</label>
          <select
            value={filters.layoutType}
            onChange={(e) => setFilters(prev => ({ ...prev, layoutType: e.target.value }))}
            className="select-input"
          >
            {layoutOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Threat Levels</label>
          <div className="threat-filters">
            {threatLevelOptions.map(option => (
              <label key={option.value} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={filters.threatLevels.includes(option.value)}
                  onChange={(e) => handleThreatFilterChange(option.value, e.target.checked)}
                />
                <span style={{ color: option.color }}>{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        <button 
          onClick={refreshData}
          className="refresh-button"
          disabled={loading}
        >
          {loading ? '⏳' : '🔄'} Refresh Graph
        </button>
      </motion.div>

      {/* Statistics */}
      {graphData.stats && (
        <motion.div 
          className="graph-stats"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <div className="stat-item">
            <span className="stat-icon">🔗</span>
            <span className="stat-label">Total Nodes</span>
            <span className="stat-value">{graphData.stats.total_nodes || 0}</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">🕸️</span>
            <span className="stat-label">Total Edges</span>
            <span className="stat-value">{graphData.stats.total_edges || 0}</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">🔗</span>
            <span className="stat-label">Internal Links</span>
            <span className="stat-value">{graphData.stats.internal_links || 0}</span>
          </div>
          <div className="stat-item">
            <span className="stat-icon">🌐</span>
            <span className="stat-label">External Links</span>
            <span className="stat-value">{graphData.stats.external_links || 0}</span>
          </div>
        </motion.div>
      )}

      {/* Graph Visualization */}
      <motion.div 
        className="graph-container"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.6 }}
      >
        {loading ? (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading network graph...</p>
          </div>
        ) : (
          <Plot
            data={plotData.data}
            layout={plotData.layout}
            config={{
              displayModeBar: true,
              modeBarButtonsToRemove: ['pan2d', 'lasso2d'],
              displaylogo: false,
              responsive: true
            }}
            style={{ width: '100%', height: '750px' }}
          />
        )}
      </motion.div>

      {/* Analytics Section */}
      {analytics && (
        <motion.div 
          className="analytics-section"
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.7 }}
        >
          <h3>🔍 Link Analytics</h3>
          
          {analytics.top_nodes && analytics.top_nodes.length > 0 && (
            <div className="analytics-card">
              <h4>🌟 Most Connected Sites</h4>
              <div className="top-nodes-list">
                {analytics.top_nodes.slice(0, 5).map((node, index) => (
                  <motion.div 
                    key={node.url}
                    className="node-item"
                    whileHover={{ x: 10 }}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.8 + index * 0.1 }}
                  >
                    <div className="node-info">
                      <div className="node-title">{node.title?.slice(0, 50) || 'No Title'}</div>
                      <div className="node-url">{node.url?.slice(0, 60)}...</div>
                    </div>
                    <div className="node-stats">
                      <span className={`threat-badge ${node.threat_level?.toLowerCase()}`}>
                        {node.threat_level}
                      </span>
                      <span className="connections">
                        {node.incoming_links || 0}↓ {node.outgoing_links || 0}↑
                      </span>
                      <span className="centrality">
                        {(node.centrality_score || 0).toFixed(2)}
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {analytics.recent_nodes && analytics.recent_nodes.length > 0 && (
            <div className="analytics-card">
              <h4>🆕 Recently Discovered</h4>
              <div className="recent-nodes-list">
                {analytics.recent_nodes.slice(0, 10).map((node, index) => (
                  <motion.div 
                    key={node.url}
                    className="recent-node-item"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.9 + index * 0.05 }}
                  >
                    <div className="recent-node-info">
                      <span className="recent-node-title">{node.title?.slice(0, 40) || 'No Title'}</span>
                      <span className="recent-node-url">{node.url?.slice(0, 50)}...</span>
                    </div>
                    <div className="recent-node-meta">
                      <span className={`threat-badge ${node.threat_level?.toLowerCase()}`}>
                        {node.threat_level}
                      </span>
                      <span className="discovery-date">{node.discovery_date}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
};

export default LinkMap;
