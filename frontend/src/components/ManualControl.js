import React, { useState, useEffect } from 'react';
import './ManualControl.css';

const ManualControl = () => {
    const [stealthMode, setStealthMode] = useState(false);
    const [pendingReviews, setPendingReviews] = useState([]);
    const [selectedItem, setSelectedItem] = useState(null);
    const [annotation, setAnnotation] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [operationalStatus, setOperationalStatus] = useState('AUTOMATED');

    useEffect(() => {
        fetchPendingReviews();
        fetchSystemStatus();
    }, []);

    const fetchPendingReviews = async () => {
        try {
            const response = await fetch('/api/manual/pending-reviews');
            const data = await response.json();
            if (data.success) {
                setPendingReviews(data.data);
            }
        } catch (error) {
            console.error('Error fetching pending reviews:', error);
        }
    };

    const fetchSystemStatus = async () => {
        try {
            const response = await fetch('/api/manual/status');
            const data = await response.json();
            if (data.success) {
                setStealthMode(data.stealth_mode);
                setOperationalStatus(data.operational_status);
            }
        } catch (error) {
            console.error('Error fetching system status:', error);
        }
    };

    const toggleStealthMode = async () => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/manual/toggle-stealth', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ stealth_mode: !stealthMode })
            });
            const data = await response.json();
            if (data.success) {
                setStealthMode(!stealthMode);
                setOperationalStatus(data.operational_status);
            }
        } catch (error) {
            console.error('Error toggling stealth mode:', error);
        }
        setIsLoading(false);
    };

    const reviewItem = (item) => {
        setSelectedItem(item);
        setAnnotation('');
    };

    const submitReview = async () => {
        if (!selectedItem || !annotation.trim()) return;

        setIsLoading(true);
        try {
            const response = await fetch('/api/manual/submit-review', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    item_id: selectedItem.id,
                    annotation: annotation,
                    reviewer: 'analyst',
                    action: 'reviewed'
                })
            });
            const data = await response.json();
            if (data.success) {
                // Remove reviewed item from pending list
                setPendingReviews(prev => prev.filter(item => item.id !== selectedItem.id));
                setSelectedItem(null);
                setAnnotation('');
            }
        } catch (error) {
            console.error('Error submitting review:', error);
        }
        setIsLoading(false);
    };

    const pauseAutomation = async () => {
        try {
            const response = await fetch('/api/manual/pause-automation', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                setOperationalStatus('PAUSED');
            }
        } catch (error) {
            console.error('Error pausing automation:', error);
        }
    };

    const resumeAutomation = async () => {
        try {
            const response = await fetch('/api/manual/resume-automation', {
                method: 'POST'
            });
            const data = await response.json();
            if (data.success) {
                setOperationalStatus('AUTOMATED');
            }
        } catch (error) {
            console.error('Error resuming automation:', error);
        }
    };

    return (
        <div className="manual-control-container">
            <div className="control-header">
                <h2>🔧 Manual Control & Stealth Operations</h2>
                <div className="status-indicators">
                    <div className={`status-badge ${operationalStatus.toLowerCase()}`}>
                        {operationalStatus}
                    </div>
                    <div className={`stealth-badge ${stealthMode ? 'active' : 'inactive'}`}>
                        {stealthMode ? '🥷 STEALTH ON' : '👁️ NORMAL MODE'}
                    </div>
                </div>
            </div>

            <div className="control-panel">
                <div className="control-section">
                    <h3>Operation Controls</h3>
                    <div className="control-buttons">
                        <button 
                            onClick={toggleStealthMode}
                            disabled={isLoading}
                            className={`btn ${stealthMode ? 'btn-warning' : 'btn-primary'}`}
                        >
                            {stealthMode ? 'Disable Stealth Mode' : 'Enable Stealth Mode'}
                        </button>
                        
                        {operationalStatus === 'AUTOMATED' ? (
                            <button onClick={pauseAutomation} className="btn btn-danger">
                                ⏸️ Pause Automation
                            </button>
                        ) : (
                            <button onClick={resumeAutomation} className="btn btn-success">
                                ▶️ Resume Automation
                            </button>
                        )}
                    </div>
                </div>

                <div className="stealth-info">
                    <h4>Stealth Mode Features</h4>
                    <ul>
                        <li>🕵️ Enhanced anonymization protocols</li>
                        <li>🔄 Randomized timing patterns</li>
                        <li>👤 Dynamic user agent rotation</li>
                        <li>🛡️ Advanced proxy chaining</li>
                        <li>📱 Covert communication channels</li>
                    </ul>
                </div>
            </div>

            <div className="review-section">
                <h3>Pending Human Review ({pendingReviews.length})</h3>
                <div className="pending-items">
                    {pendingReviews.length === 0 ? (
                        <div className="no-items">
                            <p>✅ No items pending review</p>
                        </div>
                    ) : (
                        pendingReviews.map(item => (
                            <div key={item.id} className="review-item">
                                <div className="item-info">
                                    <div className="item-url">{item.url}</div>
                                    <div className="item-details">
                                        <span className={`threat-level ${item.threat_level.toLowerCase()}`}>
                                            {item.threat_level}
                                        </span>
                                        <span className="confidence">
                                            Confidence: {(item.confidence_score * 100).toFixed(1)}%
                                        </span>
                                        <span className="timestamp">
                                            {new Date(item.timestamp).toLocaleString()}
                                        </span>
                                    </div>
                                    <div className="item-summary">{item.analysis_summary}</div>
                                </div>
                                <div className="item-actions">
                                    <button 
                                        onClick={() => reviewItem(item)}
                                        className="btn btn-primary btn-sm"
                                    >
                                        Review
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {selectedItem && (
                <div className="review-modal">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h4>Review Item</h4>
                            <button 
                                onClick={() => setSelectedItem(null)}
                                className="close-btn"
                            >
                                ×
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="item-details">
                                <p><strong>URL:</strong> {selectedItem.url}</p>
                                <p><strong>Threat Level:</strong> 
                                    <span className={`threat-level ${selectedItem.threat_level.toLowerCase()}`}>
                                        {selectedItem.threat_level}
                                    </span>
                                </p>
                                <p><strong>AI Summary:</strong> {selectedItem.analysis_summary}</p>
                                <p><strong>Confidence:</strong> {(selectedItem.confidence_score * 100).toFixed(1)}%</p>
                            </div>
                            <div className="annotation-section">
                                <label>Analyst Annotation:</label>
                                <textarea
                                    value={annotation}
                                    onChange={(e) => setAnnotation(e.target.value)}
                                    placeholder="Add your analysis and recommendations..."
                                    rows={4}
                                    className="annotation-textarea"
                                />
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button 
                                onClick={submitReview}
                                disabled={!annotation.trim() || isLoading}
                                className="btn btn-success"
                            >
                                Submit Review
                            </button>
                            <button 
                                onClick={() => setSelectedItem(null)}
                                className="btn btn-secondary"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ManualControl;
