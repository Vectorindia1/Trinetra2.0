"""
TRINETRA - Law Enforcement Incident Reporting System
Generates detailed incident reports for law enforcement agencies
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database.models import db_manager
import hashlib
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IncidentEvidence:
    """Evidence item for incident reports"""
    evidence_type: str  # 'url', 'screenshot', 'metadata', 'ai_analysis'
    evidence_value: str
    timestamp: str
    confidence_level: float
    chain_of_custody: List[str]
    description: str


@dataclass
class IncidentReport:
    """Complete incident report for law enforcement"""
    incident_id: str
    report_date: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    classification: str  # e.g., 'drug_trafficking', 'weapons', 'terrorism'
    summary: str
    detailed_description: str
    evidence_items: List[IncidentEvidence]
    suspects: List[Dict]
    geographical_data: List[Dict]
    communication_channels: List[Dict]
    recommendations: List[str]
    investigating_officer: str
    report_status: str  # DRAFT, SUBMITTED, UNDER_REVIEW, CLOSED


class LawEnforcementReporter:
    """Generates detailed incident reports for law enforcement"""
    
    def __init__(self):
        self.report_templates = self._load_report_templates()
    
    def _load_report_templates(self) -> Dict:
        """Load report templates for different types of incidents"""
        return {
            "drug_trafficking": {
                "keywords": ["drugs", "cocaine", "heroin", "meth", "fentanyl", "marijuana", "pills"],
                "severity_threshold": "MEDIUM",
                "required_evidence": ["url", "ai_analysis", "metadata"]
            },
            "weapons_trafficking": {
                "keywords": ["weapon", "gun", "rifle", "pistol", "explosive", "bomb", "ammunition"],
                "severity_threshold": "HIGH",
                "required_evidence": ["url", "ai_analysis", "screenshot"]
            },
            "terrorism": {
                "keywords": ["terrorism", "terrorist", "attack", "bomb", "isis", "al-qaeda"],
                "severity_threshold": "CRITICAL",
                "required_evidence": ["url", "ai_analysis", "metadata", "screenshot"]
            },
            "human_trafficking": {
                "keywords": ["human trafficking", "forced labor", "sex trafficking", "slavery"],
                "severity_threshold": "CRITICAL",
                "required_evidence": ["url", "ai_analysis", "geographical_data"]
            },
            "cybercrime": {
                "keywords": ["hacking", "malware", "ransomware", "carding", "phishing", "ddos"],
                "severity_threshold": "MEDIUM",
                "required_evidence": ["url", "ai_analysis", "technical_metadata"]
            },
            "financial_crimes": {
                "keywords": ["money laundering", "bitcoin mixer", "crypto tumbler", "fraud"],
                "severity_threshold": "HIGH",
                "required_evidence": ["url", "ai_analysis", "financial_metadata"]
            }
        }
    
    def generate_incident_report(self, alert_ids: List[int], incident_type: str, 
                               investigating_officer: str = "System Generated") -> IncidentReport:
        """Generate a comprehensive incident report from multiple alerts"""
        
        # Generate unique incident ID
        incident_id = f"TRINETRA-{datetime.now().strftime('%Y%m%d')}-{hashlib.md5(str(alert_ids).encode()).hexdigest()[:8].upper()}"
        
        # Gather all related data
        alerts = self._get_alerts_data(alert_ids)
        ai_analyses = self._get_ai_analyses_for_alerts(alert_ids)
        metadata = self._collect_metadata(alerts)
        
        # Classify incident
        classification = self._classify_incident(alerts, ai_analyses, incident_type)
        
        # Determine severity
        severity = self._determine_incident_severity(alerts, ai_analyses, classification)
        
        # Generate summary and description
        summary = self._generate_summary(alerts, classification)
        detailed_description = self._generate_detailed_description(alerts, ai_analyses, metadata)
        
        # Collect evidence
        evidence_items = self._collect_evidence(alerts, ai_analyses, metadata)
        
        # Extract suspects and geographical data
        suspects = self._extract_suspects(metadata)
        geographical_data = self._extract_geographical_data(metadata)
        communication_channels = self._extract_communication_channels(metadata)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(classification, severity, evidence_items)
        
        # Create incident report
        incident_report = IncidentReport(
            incident_id=incident_id,
            report_date=datetime.now().isoformat(),
            severity=severity,
            classification=classification,
            summary=summary,
            detailed_description=detailed_description,
            evidence_items=evidence_items,
            suspects=suspects,
            geographical_data=geographical_data,
            communication_channels=communication_channels,
            recommendations=recommendations,
            investigating_officer=investigating_officer,
            report_status="DRAFT"
        )
        
        # Store report in database
        self._store_incident_report(incident_report)
        
        return incident_report
    
    def _get_alerts_data(self, alert_ids: List[int]) -> List[Dict]:
        """Retrieve alert data from database"""
        try:
            with db_manager.get_cursor() as cursor:
                placeholders = ','.join(['?' for _ in alert_ids])
                cursor.execute(f"""
                    SELECT * FROM alerts WHERE id IN ({placeholders})
                    ORDER BY timestamp DESC
                """, alert_ids)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving alerts data: {e}")
            return []
    
    def _get_ai_analyses_for_alerts(self, alert_ids: List[int]) -> List[Dict]:
        """Get AI analyses related to the alerts"""
        try:
            with db_manager.get_cursor() as cursor:
                placeholders = ','.join(['?' for _ in alert_ids])
                cursor.execute(f"""
                    SELECT ai.* FROM ai_analysis ai
                    JOIN alerts a ON ai.url = a.url
                    WHERE a.id IN ({placeholders})
                    ORDER BY ai.processed_at DESC
                """, alert_ids)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving AI analyses: {e}")
            return []
    
    def _collect_metadata(self, alerts: List[Dict]) -> Dict:
        """Collect metadata from various sources"""
        metadata = {
            "emails": set(),
            "ips": set(),
            "chatrooms": set(),
            "urls": [alert['url'] for alert in alerts],
            "timestamps": [alert['timestamp'] for alert in alerts]
        }
        
        # Collect metadata from crawled pages and other sources
        try:
            with db_manager.get_cursor() as cursor:
                for alert in alerts:
                    # Get metadata from non_http_links table
                    cursor.execute("""
                        SELECT link_type, link_value FROM non_http_links 
                        WHERE source_url = ?
                    """, (alert['url'],))
                    
                    for row in cursor.fetchall():
                        link_type, link_value = row
                        if link_type == 'email':
                            metadata['emails'].add(link_value)
                        elif link_type == 'ip':
                            metadata['ips'].add(link_value)
                
                # Get chatroom links
                cursor.execute("""
                    SELECT chatroom_url FROM chatroom_links 
                    WHERE source_url IN ({})
                """.format(','.join(['?' for _ in alerts])), [alert['url'] for alert in alerts])
                
                for row in cursor.fetchall():
                    metadata['chatrooms'].add(row[0])
                    
        except Exception as e:
            logger.error(f"Error collecting metadata: {e}")
        
        return {k: list(v) if isinstance(v, set) else v for k, v in metadata.items()}
    
    def _classify_incident(self, alerts: List[Dict], ai_analyses: List[Dict], 
                          incident_type: str) -> str:
        """Classify the incident type based on evidence"""
        
        # Use provided incident_type if valid
        if incident_type in self.report_templates:
            return incident_type
        
        # Auto-classify based on AI analyses and keywords
        classification_scores = {}
        
        for template_name, template in self.report_templates.items():
            score = 0
            
            # Check AI analyses
            for analysis in ai_analyses:
                threat_categories = analysis.get('threat_categories', [])
                if isinstance(threat_categories, str):
                    try:
                        threat_categories = json.loads(threat_categories)
                    except:
                        threat_categories = []
                
                # Score based on keyword matches
                for keyword in template['keywords']:
                    for category in threat_categories:
                        if keyword.lower() in category.lower():
                            score += 1
            
            # Check alert keywords
            for alert in alerts:
                alert_keywords = alert.get('keywords_found', [])
                if isinstance(alert_keywords, str):
                    try:
                        alert_keywords = json.loads(alert_keywords)
                    except:
                        alert_keywords = []
                
                for keyword in template['keywords']:
                    for alert_keyword in alert_keywords:
                        if keyword.lower() in alert_keyword.lower():
                            score += 1
            
            classification_scores[template_name] = score
        
        # Return the classification with the highest score
        if classification_scores:
            return max(classification_scores, key=classification_scores.get)
        else:
            return "cybercrime"  # Default classification
    
    def _determine_incident_severity(self, alerts: List[Dict], ai_analyses: List[Dict], 
                                   classification: str) -> str:
        """Determine incident severity based on evidence"""
        
        # Base severity from template
        base_severity = self.report_templates.get(classification, {}).get('severity_threshold', 'MEDIUM')
        
        # Severity scoring
        severity_score = 0
        
        # AI analysis threat levels
        critical_count = sum(1 for analysis in ai_analyses if analysis.get('threat_level') == 'CRITICAL')
        high_count = sum(1 for analysis in ai_analyses if analysis.get('threat_level') == 'HIGH')
        
        if critical_count > 0:
            severity_score += 10
        if high_count > 0:
            severity_score += 5
        
        # Confidence scores
        high_confidence_count = sum(1 for analysis in ai_analyses if analysis.get('confidence_score', 0) > 0.8)
        if high_confidence_count > 0:
            severity_score += 3
        
        # Number of alerts
        if len(alerts) > 10:
            severity_score += 5
        elif len(alerts) > 5:
            severity_score += 2
        
        # Determine final severity
        if severity_score >= 15 or base_severity == 'CRITICAL':
            return 'CRITICAL'
        elif severity_score >= 8 or base_severity == 'HIGH':
            return 'HIGH'
        elif severity_score >= 3 or base_severity == 'MEDIUM':
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_summary(self, alerts: List[Dict], classification: str) -> str:
        """Generate incident summary"""
        
        alert_count = len(alerts)
        urls = [alert['url'] for alert in alerts[:3]]  # First 3 URLs
        
        summary = f"""AUTOMATED INCIDENT REPORT - {classification.upper().replace('_', ' ')}
        
Incident involves {alert_count} detected alerts across multiple darknet sources.
Primary URLs under investigation: {', '.join(urls)}

This incident has been automatically classified as {classification.replace('_', ' ')} 
based on AI analysis and keyword detection patterns.

Immediate law enforcement review recommended for threat assessment and 
potential criminal investigation initiation."""
        
        return summary
    
    def _generate_detailed_description(self, alerts: List[Dict], ai_analyses: List[Dict], 
                                     metadata: Dict) -> str:
        """Generate detailed incident description"""
        
        description = f"""DETAILED INCIDENT ANALYSIS

=== OVERVIEW ===
This incident encompasses {len(alerts)} detected alerts and {len(ai_analyses)} AI analyses 
from darknet surveillance operations conducted by TRINETRA system.

=== ALERT BREAKDOWN ===
"""
        
        for i, alert in enumerate(alerts[:5], 1):  # Limit to first 5 alerts
            description += f"""
Alert #{i}:
  URL: {alert['url']}
  Timestamp: {alert['timestamp']}
  Threat Level: {alert.get('threat_level', 'UNKNOWN')}
  Keywords: {alert.get('keywords_found', 'None')}
"""
        
        if len(alerts) > 5:
            description += f"\n... and {len(alerts) - 5} additional alerts\n"
        
        description += "\n=== AI ANALYSIS SUMMARY ===\n"
        
        threat_levels = {}
        for analysis in ai_analyses:
            level = analysis.get('threat_level', 'UNKNOWN')
            threat_levels[level] = threat_levels.get(level, 0) + 1
        
        for level, count in threat_levels.items():
            description += f"  {level}: {count} instances\n"
        
        description += f"""

=== METADATA SUMMARY ===
Emails detected: {len(metadata.get('emails', []))}
IP addresses detected: {len(metadata.get('ips', []))}
Chatroom links detected: {len(metadata.get('chatrooms', []))}

=== INVESTIGATION PRIORITY ===
This incident requires immediate law enforcement attention due to the 
automated classification and threat indicators identified.
"""
        
        return description
    
    def _collect_evidence(self, alerts: List[Dict], ai_analyses: List[Dict], 
                         metadata: Dict) -> List[IncidentEvidence]:
        """Collect evidence items for the incident"""
        
        evidence_items = []
        
        # URL evidence
        for alert in alerts:
            evidence_items.append(IncidentEvidence(
                evidence_type="url",
                evidence_value=alert['url'],
                timestamp=alert['timestamp'],
                confidence_level=0.9,
                chain_of_custody=["TRINETRA_SYSTEM", "AUTOMATED_CRAWLER"],
                description=f"Darknet URL flagged by keyword detection: {alert.get('keywords_found', 'N/A')}"
            ))
        
        # AI analysis evidence
        for analysis in ai_analyses:
            evidence_items.append(IncidentEvidence(
                evidence_type="ai_analysis",
                evidence_value=json.dumps({
                    "threat_level": analysis.get('threat_level'),
                    "confidence_score": analysis.get('confidence_score'),
                    "summary": analysis.get('analysis_summary')
                }),
                timestamp=analysis.get('processed_at', datetime.now().isoformat()),
                confidence_level=analysis.get('confidence_score', 0.0),
                chain_of_custody=["TRINETRA_SYSTEM", "GEMINI_AI_ANALYZER"],
                description=f"AI threat analysis: {analysis.get('analysis_summary', 'No summary available')}"
            ))
        
        # Metadata evidence
        for email in metadata.get('emails', []):
            evidence_items.append(IncidentEvidence(
                evidence_type="email_address",
                evidence_value=email,
                timestamp=datetime.now().isoformat(),
                confidence_level=0.8,
                chain_of_custody=["TRINETRA_SYSTEM", "METADATA_EXTRACTOR"],
                description="Email address extracted from darknet content"
            ))
        
        for ip in metadata.get('ips', []):
            evidence_items.append(IncidentEvidence(
                evidence_type="ip_address",
                evidence_value=ip,
                timestamp=datetime.now().isoformat(),
                confidence_level=0.8,
                chain_of_custody=["TRINETRA_SYSTEM", "METADATA_EXTRACTOR"],
                description="IP address extracted from darknet content"
            ))
        
        return evidence_items
    
    def _extract_suspects(self, metadata: Dict) -> List[Dict]:
        """Extract potential suspect information"""
        
        suspects = []
        
        # Create suspect profiles from email addresses
        for email in metadata.get('emails', []):
            suspects.append({
                "identifier": email,
                "identifier_type": "email",
                "confidence": 0.6,
                "source": "darknet_content_extraction",
                "additional_info": "Email address found in monitored darknet content"
            })
        
        # Create suspect profiles from unique IPs
        for ip in metadata.get('ips', []):
            suspects.append({
                "identifier": ip,
                "identifier_type": "ip_address",
                "confidence": 0.5,
                "source": "darknet_content_extraction",
                "additional_info": "IP address extracted from darknet communications"
            })
        
        return suspects
    
    def _extract_geographical_data(self, metadata: Dict) -> List[Dict]:
        """Extract geographical intelligence"""
        
        geo_data = []
        
        # This would integrate with actual geolocation service
        # For now, providing placeholder structure
        for ip in metadata.get('ips', []):
            geo_data.append({
                "ip_address": ip,
                "country": "Unknown",
                "region": "Unknown",
                "city": "Unknown",
                "latitude": None,
                "longitude": None,
                "confidence": 0.0,
                "source": "geolocation_service"
            })
        
        return geo_data
    
    def _extract_communication_channels(self, metadata: Dict) -> List[Dict]:
        """Extract communication channel information"""
        
        channels = []
        
        # Chatroom channels
        for chatroom in metadata.get('chatrooms', []):
            channels.append({
                "channel_type": "chatroom",
                "channel_identifier": chatroom,
                "platform": "unknown",
                "risk_level": "HIGH",
                "monitoring_status": "detected"
            })
        
        return channels
    
    def _generate_recommendations(self, classification: str, severity: str, 
                                evidence_items: List[IncidentEvidence]) -> List[str]:
        """Generate investigation recommendations"""
        
        recommendations = [
            "Immediate law enforcement review required",
            "Preserve all digital evidence with proper chain of custody",
            "Consider coordinating with relevant international agencies",
            "Monitor associated IP addresses and email addresses",
            "Review related surveillance data for additional evidence"
        ]
        
        # Classification-specific recommendations
        if classification == "terrorism":
            recommendations.extend([
                "URGENT: Coordinate with counter-terrorism units",
                "Consider national security implications",
                "Escalate to appropriate federal agencies immediately"
            ])
        elif classification == "drug_trafficking":
            recommendations.extend([
                "Coordinate with narcotics enforcement divisions",
                "Monitor for transaction patterns and payment methods",
                "Consider undercover investigation opportunities"
            ])
        elif classification == "weapons_trafficking":
            recommendations.extend([
                "Alert firearms enforcement agencies",
                "Monitor for delivery and logistics patterns",
                "Consider international weapons trafficking implications"
            ])
        elif classification == "human_trafficking":
            recommendations.extend([
                "URGENT: Coordinate with human trafficking task forces",
                "Prioritize victim identification and rescue operations",
                "Consider international trafficking implications"
            ])
        
        # Severity-specific recommendations
        if severity == "CRITICAL":
            recommendations.insert(0, "🚨 CRITICAL PRIORITY: Immediate action required within 1 hour")
        elif severity == "HIGH":
            recommendations.insert(0, "⚠️ HIGH PRIORITY: Action required within 24 hours")
        
        return recommendations
    
    def _store_incident_report(self, incident_report: IncidentReport):
        """Store incident report in database"""
        
        try:
            with db_manager.get_cursor() as cursor:
                # Create incident_reports table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS incident_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        incident_id TEXT UNIQUE NOT NULL,
                        report_date TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        classification TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        detailed_description TEXT NOT NULL,
                        evidence_items TEXT NOT NULL,
                        suspects TEXT NOT NULL,
                        geographical_data TEXT NOT NULL,
                        communication_channels TEXT NOT NULL,
                        recommendations TEXT NOT NULL,
                        investigating_officer TEXT NOT NULL,
                        report_status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert the incident report
                cursor.execute("""
                    INSERT OR REPLACE INTO incident_reports (
                        incident_id, report_date, severity, classification, summary,
                        detailed_description, evidence_items, suspects, geographical_data,
                        communication_channels, recommendations, investigating_officer, report_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    incident_report.incident_id,
                    incident_report.report_date,
                    incident_report.severity,
                    incident_report.classification,
                    incident_report.summary,
                    incident_report.detailed_description,
                    json.dumps([asdict(item) for item in incident_report.evidence_items]),
                    json.dumps(incident_report.suspects),
                    json.dumps(incident_report.geographical_data),
                    json.dumps(incident_report.communication_channels),
                    json.dumps(incident_report.recommendations),
                    incident_report.investigating_officer,
                    incident_report.report_status
                ))
                
                logger.info(f"Stored incident report: {incident_report.incident_id}")
                
        except Exception as e:
            logger.error(f"Error storing incident report: {e}")
            raise
    
    def get_incident_reports(self, limit: int = 50, status: str = None) -> List[Dict]:
        """Retrieve incident reports from database"""
        
        try:
            with db_manager.get_cursor() as cursor:
                if status:
                    cursor.execute("""
                        SELECT * FROM incident_reports 
                        WHERE report_status = ?
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (status, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM incident_reports 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """, (limit,))
                
                reports = []
                for row in cursor.fetchall():
                    report_dict = dict(row)
                    # Parse JSON fields
                    for json_field in ['evidence_items', 'suspects', 'geographical_data', 
                                     'communication_channels', 'recommendations']:
                        try:
                            report_dict[json_field] = json.loads(report_dict[json_field])
                        except:
                            report_dict[json_field] = []
                    reports.append(report_dict)
                
                return reports
                
        except Exception as e:
            logger.error(f"Error retrieving incident reports: {e}")
            return []
    
    def get_incident_report(self, incident_id: str) -> Dict:
        """Get specific incident report"""
        
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM incident_reports WHERE incident_id = ?
                """, (incident_id,))
                
                row = cursor.fetchone()
                if row:
                    report_dict = dict(row)
                    # Parse JSON fields
                    for json_field in ['evidence_items', 'suspects', 'geographical_data', 
                                     'communication_channels', 'recommendations']:
                        try:
                            report_dict[json_field] = json.loads(report_dict[json_field])
                        except:
                            report_dict[json_field] = []
                    return report_dict
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving incident report {incident_id}: {e}")
            return None
    
    def update_incident_status(self, incident_id: str, status: str, notes: str = "") -> bool:
        """Update incident report status"""
        
        try:
            with db_manager.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE incident_reports 
                    SET report_status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE incident_id = ?
                """, (status, incident_id))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating incident status: {e}")
            return False
    
    def export_incident_report(self, incident_id: str, format: str = "json") -> str:
        """Export incident report in specified format"""
        
        report = self.get_incident_report(incident_id)
        if not report:
            raise ValueError(f"Incident report {incident_id} not found")
        
        if format == "json":
            return json.dumps(report, indent=2)
        elif format == "pdf":
            # This would integrate with a PDF generation library
            # For now, return JSON as placeholder
            return json.dumps(report, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global instance
incident_reporter = LawEnforcementReporter()
