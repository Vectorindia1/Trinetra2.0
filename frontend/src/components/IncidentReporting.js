import React, { useState, useEffect } from 'react';
import './IncidentReporting.css';

const IncidentReporting = () => {
    const [incidentReports, setIncidentReports] = useState([]);
    const [selectedReport, setSelectedReport] = useState(null);
    const [alerts, setAlerts] = useState([]);
    const [selectedAlerts, setSelectedAlerts] = useState([]);
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [newReport, setNewReport] = useState({
        incident_type: 'cybercrime',
        investigating_officer: '',
        notes: ''
    });

    useEffect(() => {
        fetchIncidentReports();
        fetchAlerts();
    }, []);

    const fetchIncidentReports = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/incidents/list');
            const data = await response.json();
            if (data.success) {
                setIncidentReports(data.data);
            }
        } catch (error) {
            console.error('Error fetching incident reports:', error);
        }
    };

    const fetchAlerts = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/alerts?limit=100');
            const data = await response.json();
            if (data.success) {
                setAlerts(data.data);
            }
        } catch (error) {
            console.error('Error fetching alerts:', error);
        }
    };

    const createIncidentReport = async () => {
        if (selectedAlerts.length === 0) {
            alert('Please select at least one alert to create an incident report.');
            return;
        }

        setIsLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/incidents/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    alert_ids: selectedAlerts,
                    incident_type: newReport.incident_type,
                    investigating_officer: newReport.investigating_officer || 'System Generated'
                })
            });

            const data = await response.json();
            if (data.success) {
                setCreateModalOpen(false);
                setSelectedAlerts([]);
                setNewReport({
                    incident_type: 'cybercrime',
                    investigating_officer: '',
                    notes: ''
                });
                fetchIncidentReports();
                alert('Incident report created successfully!');
            } else {
                alert('Failed to create incident report: ' + data.message);
            }
        } catch (error) {
            console.error('Error creating incident report:', error);
            alert('Error creating incident report');
        }
        setIsLoading(false);
    };

    const updateReportStatus = async (incidentId, newStatus) => {
        try {
            const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: newStatus,
                    notes: 'Status updated from dashboard'
                })
            });

            const data = await response.json();
            if (data.success) {
                fetchIncidentReports();
                alert('Report status updated successfully!');
            }
        } catch (error) {
            console.error('Error updating report status:', error);
        }
    };

    const exportReport = async (incidentId, format = 'json') => {
        try {
            const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}/export?format=${format}`);
            const data = await response.json();
            
            if (data.success) {
                // Create download link
                const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `incident_${incidentId}.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            }
        } catch (error) {
            console.error('Error exporting report:', error);
        }
    };

    const toggleAlertSelection = (alertId) => {
        setSelectedAlerts(prev => 
            prev.includes(alertId) 
                ? prev.filter(id => id !== alertId)
                : [...prev, alertId]
        );
    };

    const getSeverityColor = (severity) => {
        switch (severity) {
            case 'CRITICAL': return '#dc2626';
            case 'HIGH': return '#f59e0b';
            case 'MEDIUM': return '#3b82f6';
            case 'LOW': return '#22c55e';
            default: return '#6b7280';
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'DRAFT': return '#6b7280';
            case 'SUBMITTED': return '#3b82f6';
            case 'UNDER_REVIEW': return '#f59e0b';
            case 'CLOSED': return '#22c55e';
            default: return '#6b7280';
        }
    };

    return (
        <div className="incident-reporting-container">
            <div className="reporting-header">
                <h2>🚨 Law Enforcement Incident Reporting</h2>
                <button 
                    onClick={() => setCreateModalOpen(true)}
                    className="btn btn-primary"
                >
                    + Create New Report
                </button>
            </div>

            <div className="reports-grid">
                <div className="reports-list">
                    <h3>Incident Reports ({incidentReports.length})</h3>
                    <div className="reports-container">
                        {incidentReports.length === 0 ? (
                            <div className="no-reports">
                                <p>No incident reports found</p>
                            </div>
                        ) : (
                            incidentReports.map(report => (
                                <div 
                                    key={report.incident_id} 
                                    className={`report-card ${selectedReport?.incident_id === report.incident_id ? 'selected' : ''}`}
                                    onClick={() => setSelectedReport(report)}
                                >
                                    <div className="report-header">
                                        <h4>{report.incident_id}</h4>
                                        <div className="report-badges">
                                            <span 
                                                className="severity-badge"
                                                style={{ backgroundColor: getSeverityColor(report.severity) }}
                                            >
                                                {report.severity}
                                            </span>
                                            <span 
                                                className="status-badge"
                                                style={{ backgroundColor: getStatusColor(report.report_status) }}
                                            >
                                                {report.report_status}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="report-meta">
                                        <p><strong>Classification:</strong> {report.classification.replace('_', ' ')}</p>
                                        <p><strong>Officer:</strong> {report.investigating_officer}</p>
                                        <p><strong>Created:</strong> {new Date(report.created_at).toLocaleString()}</p>
                                        <p><strong>Evidence Items:</strong> {report.evidence_items?.length || 0}</p>
                                    </div>
                                    <div className="report-actions">
                                        <button 
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                exportReport(report.incident_id);
                                            }}
                                            className="btn btn-sm btn-secondary"
                                        >
                                            Export
                                        </button>
                                        {report.report_status === 'DRAFT' && (
                                            <button 
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    updateReportStatus(report.incident_id, 'SUBMITTED');
                                                }}
                                                className="btn btn-sm btn-primary"
                                            >
                                                Submit
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {selectedReport && (
                    <div className="report-details">
                        <h3>Report Details</h3>
                        <div className="report-content">
                            <div className="detail-section">
                                <h4>Summary</h4>
                                <div className="summary-content">
                                    {selectedReport.summary}
                                </div>
                            </div>

                            <div className="detail-section">
                                <h4>Detailed Description</h4>
                                <div className="description-content">
                                    <pre>{selectedReport.detailed_description}</pre>
                                </div>
                            </div>

                            <div className="detail-section">
                                <h4>Evidence Items ({selectedReport.evidence_items?.length || 0})</h4>
                                <div className="evidence-list">
                                    {selectedReport.evidence_items?.map((evidence, index) => (
                                        <div key={index} className="evidence-item">
                                            <div className="evidence-header">
                                                <span className="evidence-type">{evidence.evidence_type}</span>
                                                <span className="confidence">
                                                    Confidence: {(evidence.confidence_level * 100).toFixed(1)}%
                                                </span>
                                            </div>
                                            <div className="evidence-description">
                                                {evidence.description}
                                            </div>
                                            <div className="evidence-timestamp">
                                                {new Date(evidence.timestamp).toLocaleString()}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="detail-section">
                                <h4>Recommendations</h4>
                                <div className="recommendations-list">
                                    {selectedReport.recommendations?.map((rec, index) => (
                                        <div key={index} className="recommendation-item">
                                            <span className="rec-number">{index + 1}.</span>
                                            <span className="rec-text">{rec}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="detail-section">
                                <h4>Suspects ({selectedReport.suspects?.length || 0})</h4>
                                <div className="suspects-list">
                                    {selectedReport.suspects?.map((suspect, index) => (
                                        <div key={index} className="suspect-item">
                                            <strong>{suspect.identifier_type}:</strong> {suspect.identifier}
                                            <span className="confidence">
                                                (Confidence: {(suspect.confidence * 100).toFixed(1)}%)
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Create Report Modal */}
            {createModalOpen && (
                <div className="modal-overlay">
                    <div className="modal-content create-report-modal">
                        <div className="modal-header">
                            <h3>Create New Incident Report</h3>
                            <button 
                                onClick={() => setCreateModalOpen(false)}
                                className="close-btn"
                            >
                                ×
                            </button>
                        </div>

                        <div className="modal-body">
                            <div className="form-group">
                                <label>Incident Type:</label>
                                <select 
                                    value={newReport.incident_type}
                                    onChange={(e) => setNewReport({...newReport, incident_type: e.target.value})}
                                    className="form-control"
                                >
                                    <option value="cybercrime">Cybercrime</option>
                                    <option value="drug_trafficking">Drug Trafficking</option>
                                    <option value="weapons_trafficking">Weapons Trafficking</option>
                                    <option value="terrorism">Terrorism</option>
                                    <option value="human_trafficking">Human Trafficking</option>
                                    <option value="financial_crimes">Financial Crimes</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label>Investigating Officer:</label>
                                <input 
                                    type="text"
                                    value={newReport.investigating_officer}
                                    onChange={(e) => setNewReport({...newReport, investigating_officer: e.target.value})}
                                    placeholder="Enter officer name (optional)"
                                    className="form-control"
                                />
                            </div>

                            <div className="form-group">
                                <label>Select Alerts to Include:</label>
                                <div className="alerts-selection">
                                    {alerts.slice(0, 20).map(alert => (
                                        <div key={alert.id} className="alert-checkbox">
                                            <input 
                                                type="checkbox"
                                                checked={selectedAlerts.includes(alert.id)}
                                                onChange={() => toggleAlertSelection(alert.id)}
                                            />
                                            <div className="alert-info">
                                                <div className="alert-url">{alert.url}</div>
                                                <div className="alert-meta">
                                                    <span className={`threat-level ${alert.threat_level?.toLowerCase()}`}>
                                                        {alert.threat_level}
                                                    </span>
                                                    <span className="alert-date">
                                                        {new Date(alert.timestamp).toLocaleDateString()}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="selection-summary">
                                    Selected: {selectedAlerts.length} alerts
                                </div>
                            </div>
                        </div>

                        <div className="modal-footer">
                            <button 
                                onClick={createIncidentReport}
                                disabled={isLoading || selectedAlerts.length === 0}
                                className="btn btn-primary"
                            >
                                {isLoading ? 'Creating...' : 'Create Report'}
                            </button>
                            <button 
                                onClick={() => setCreateModalOpen(false)}
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

export default IncidentReporting;
