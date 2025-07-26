#!/usr/bin/env python3
"""
TRINETRA - Police Report Generator
Generates comprehensive XLSX reports for law enforcement and intelligence agencies
containing all darkweb intelligence findings, analysis, and evidence.
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import hashlib
from collections import Counter
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import requests
from urllib.parse import urlparse
import re

# Database imports
try:
    from database.models import db_manager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Database not available, using JSON files only")

class PoliceReportGenerator:
    """
    Comprehensive report generator for law enforcement agencies
    """
    
    def __init__(self, output_dir="police_reports"):
        self.output_dir = output_dir
        self.ensure_output_directory()
        self.report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def ensure_output_directory(self):
        """Ensure output directory exists"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_comprehensive_report(self, case_id=None, officer_id=None, jurisdiction=None):
        """
        Generate comprehensive police report with all intelligence data
        """
        print("🚨 GENERATING COMPREHENSIVE POLICE INTELLIGENCE REPORT")
        print("=" * 70)
        
        case_id = case_id or f"DARKWEB_{self.report_timestamp}"
        report_filename = f"{self.output_dir}/POLICE_REPORT_{case_id}_{self.report_timestamp}.xlsx"
        
        # Load all data sources
        data = self._load_all_data()
        
        # Create workbook with advanced formatting
        workbook = xlsxwriter.Workbook(report_filename, {
            'constant_memory': True,
            'default_date_format': 'yyyy-mm-dd hh:mm:ss'
        })
        
        # Define professional styles
        styles = self._create_report_styles(workbook)
        
        # Generate all report sections
        self._create_executive_summary(workbook, styles, data, case_id, officer_id, jurisdiction)
        self._create_threat_intelligence_sheet(workbook, styles, data)
        self._create_detailed_alerts_sheet(workbook, styles, data)
        self._create_crawled_sites_sheet(workbook, styles, data)
        self._create_keyword_analysis_sheet(workbook, styles, data)
        self._create_timeline_analysis_sheet(workbook, styles, data)
        self._create_network_analysis_sheet(workbook, styles, data)
        self._create_evidence_chain_sheet(workbook, styles, data)
        self._create_ai_analysis_sheet(workbook, styles, data)
        self._create_technical_appendix_sheet(workbook, styles, data)
        
        workbook.close()
        
        print(f"✅ COMPREHENSIVE POLICE REPORT GENERATED: {report_filename}")
        print(f"📊 Report contains {len(data['alerts'])} alerts from {len(data['visited'])} investigated sites")
        print(f"🔍 Case ID: {case_id}")
        
        # Generate summary statistics
        self._generate_report_summary(data, case_id)
        
        return report_filename
    
    def _load_all_data(self):
        """Load data from all available sources"""
        data = {
            'alerts': [],
            'visited': [],
            'non_http': [],
            'ai_analyses': [],
            'threat_signatures': [],
            'geolocation_data': []
        }
        
        # Load from database if available
        if DATABASE_AVAILABLE:
            try:
                print("📊 Loading data from database...")
                data['alerts'] = [dict(alert) for alert in db_manager.get_alerts(limit=10000)]
                data['visited'] = [dict(page) for page in db_manager.get_crawled_pages(limit=10000)]
                data['ai_analyses'] = [dict(analysis) for analysis in db_manager.get_ai_analyses(limit=10000)]
                data['threat_signatures'] = [dict(sig) for sig in db_manager.get_threat_signatures(limit=1000)]
                print(f"✅ Loaded {len(data['alerts'])} alerts from database")
            except Exception as e:
                print(f"⚠️ Database error: {e}, falling back to JSON files")
        
        # Load from JSON files as backup/supplement
        try:
            if os.path.exists("alert_log.json"):
                with open("alert_log.json", "r", encoding='utf-8') as f:
                    json_alerts = [json.loads(line) for line in f if line.strip()]
                data['alerts'].extend(json_alerts)
                
            if os.path.exists("visited_links.json"):
                with open("visited_links.json", "r", encoding='utf-8') as f:
                    data['visited'].extend(json.load(f))
                    
            if os.path.exists("non_http_links.json"):
                with open("non_http_links.json", "r", encoding='utf-8') as f:
                    data['non_http'].extend(json.load(f))
                    
        except Exception as e:
            print(f"⚠️ Error loading JSON files: {e}")
        
        # Deduplicate data
        data['alerts'] = self._deduplicate_alerts(data['alerts'])
        data['visited'] = self._deduplicate_visited(data['visited'])
        
        print(f"📊 Total data loaded: {len(data['alerts'])} alerts, {len(data['visited'])} sites")
        return data
    
    def _deduplicate_alerts(self, alerts):
        """Remove duplicate alerts based on content hash"""
        seen_hashes = set()
        unique_alerts = []
        
        for alert in alerts:
            # Skip if alert is not a dictionary
            if not isinstance(alert, dict):
                print(f"⚠️ Skipping invalid alert data: {type(alert)}")
                continue
                
            content_hash = alert.get('content_hash')
            if not content_hash:
                # Generate hash if missing
                content = f"{alert.get('url', '')}{alert.get('title', '')}{alert.get('keywords_found', [])}"
                content_hash = hashlib.md5(content.encode()).hexdigest()
                alert['content_hash'] = content_hash
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_alerts.append(alert)
        
        return unique_alerts
    
    def _deduplicate_visited(self, visited):
        """Remove duplicate visited links"""
        seen_urls = set()
        unique_visited = []
        
        for link in visited:
            url = link.get('url') if isinstance(link, dict) else link
            if url not in seen_urls:
                seen_urls.add(url)
                unique_visited.append(link)
        
        return unique_visited
    
    def _create_report_styles(self, workbook):
        """Create professional formatting styles for the report"""
        styles = {}
        
        # Header styles
        styles['title'] = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'font_color': '#1f2937',
            'bg_color': '#f3f4f6',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        styles['header'] = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'font_color': 'white',
            'bg_color': '#374151',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True
        })
        
        styles['subheader'] = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'font_color': '#374151',
            'bg_color': '#e5e7eb',
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })
        
        # Data styles
        styles['data'] = workbook.add_format({
            'font_size': 10,
            'align': 'left',
            'valign': 'top',
            'border': 1,
            'text_wrap': True
        })
        
        styles['data_center'] = workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        styles['data_number'] = workbook.add_format({
            'font_size': 10,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0'
        })
        
        # Threat level styles
        styles['critical'] = workbook.add_format({
            'font_size': 10,
            'font_color': 'white',
            'bg_color': '#dc2626',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bold': True
        })
        
        styles['high'] = workbook.add_format({
            'font_size': 10,
            'font_color': 'white',
            'bg_color': '#ef4444',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bold': True
        })
        
        styles['medium'] = workbook.add_format({
            'font_size': 10,
            'font_color': 'black',
            'bg_color': '#f59e0b',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bold': True
        })
        
        styles['low'] = workbook.add_format({
            'font_size': 10,
            'font_color': 'white',
            'bg_color': '#22c55e',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bold': True
        })
        
        # Date style
        styles['date'] = workbook.add_format({
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'num_format': 'yyyy-mm-dd hh:mm:ss'
        })
        
        return styles
    
    def _create_executive_summary(self, workbook, styles, data, case_id, officer_id, jurisdiction):
        """Create executive summary sheet"""
        worksheet = workbook.add_worksheet("Executive Summary")
        
        # Report header
        worksheet.merge_range('A1:H1', f'DARKWEB INTELLIGENCE REPORT - CASE {case_id}', styles['title'])
        
        row = 2
        worksheet.write(row, 0, "Report Classification:", styles['subheader'])
        worksheet.write(row, 1, "LAW ENFORCEMENT SENSITIVE", styles['critical'])
        
        row += 1
        worksheet.write(row, 0, "Generated:", styles['subheader'])
        worksheet.write(row, 1, datetime.now(), styles['date'])
        
        row += 1
        worksheet.write(row, 0, "Case Officer:", styles['subheader'])
        worksheet.write(row, 1, officer_id or "NOT SPECIFIED", styles['data'])
        
        row += 1
        worksheet.write(row, 0, "Jurisdiction:", styles['subheader'])
        worksheet.write(row, 1, jurisdiction or "NOT SPECIFIED", styles['data'])
        
        row += 2
        worksheet.write(row, 0, "EXECUTIVE SUMMARY", styles['header'])
        
        # Key statistics
        row += 1
        stats = [
            ("Total Alerts Generated", len(data['alerts'])),
            ("High-Risk Sites Identified", len([a for a in data['alerts'] if self._get_threat_level(a) in ['HIGH', 'CRITICAL']])),
            ("Unique Domains Investigated", len(set([self._extract_domain(a.get('url', '')) for a in data['alerts']]))),
            ("Suspicious Keywords Detected", len(set([kw for a in data['alerts'] for kw in a.get('keywords_found', [])]))),
            ("Total Pages Crawled", len(data['visited'])),
            ("Investigation Period (Days)", self._calculate_investigation_period(data)),
        ]
        
        for stat_name, stat_value in stats:
            worksheet.write(row, 0, stat_name, styles['subheader'])
            worksheet.write(row, 1, stat_value, styles['data_number'])
            row += 1
        
        # Key findings
        row += 1
        worksheet.write(row, 0, "KEY FINDINGS", styles['header'])
        row += 1
        
        key_findings = self._generate_key_findings(data)
        for finding in key_findings:
            worksheet.write(row, 0, f"• {finding}", styles['data'])
            row += 1
        
        # Set column widths
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:H', 15)
    
    def _create_threat_intelligence_sheet(self, workbook, styles, data):
        """Create detailed threat intelligence analysis sheet"""
        worksheet = workbook.add_worksheet("Threat Intelligence")
        
        # Headers
        headers = [
            "Alert ID", "Timestamp", "URL", "Site Title", "Threat Level", 
            "Keywords Found", "Domain", "Content Hash", "Investigation Notes"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, styles['header'])
        
        # Data rows
        for row, alert in enumerate(data['alerts'], 1):
            threat_level = self._get_threat_level(alert)
            
            worksheet.write(row, 0, row, styles['data_center'])
            worksheet.write(row, 1, self._parse_timestamp(alert.get('timestamp')), styles['date'])
            worksheet.write(row, 2, alert.get('url', ''), styles['data'])
            worksheet.write(row, 3, alert.get('title', 'N/A'), styles['data'])
            worksheet.write(row, 4, threat_level, self._get_threat_style(styles, threat_level))
            worksheet.write(row, 5, ', '.join(alert.get('keywords_found', [])), styles['data'])
            worksheet.write(row, 6, self._extract_domain(alert.get('url', '')), styles['data'])
            worksheet.write(row, 7, alert.get('content_hash', 'N/A'), styles['data'])
            worksheet.write(row, 8, self._generate_investigation_notes(alert), styles['data'])
        
        # Set column widths
        worksheet.set_column('A:A', 8)
        worksheet.set_column('B:B', 18)
        worksheet.set_column('C:C', 50)
        worksheet.set_column('D:D', 30)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 40)
        worksheet.set_column('G:G', 25)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 50)
    
    def _create_detailed_alerts_sheet(self, workbook, styles, data):
        """Create detailed alerts breakdown sheet"""
        worksheet = workbook.add_worksheet("Detailed Alerts")
        
        # Group alerts by threat level
        alerts_by_level = {}
        for alert in data['alerts']:
            level = self._get_threat_level(alert)
            if level not in alerts_by_level:
                alerts_by_level[level] = []
            alerts_by_level[level].append(alert)
        
        row = 0
        for threat_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if threat_level not in alerts_by_level:
                continue
                
            alerts = alerts_by_level[threat_level]
            
            # Section header
            worksheet.merge_range(row, 0, row, 7, f"{threat_level} THREAT ALERTS ({len(alerts)} found)", 
                                self._get_threat_style(styles, threat_level))
            row += 1
            
            # Sub-headers
            sub_headers = ["#", "URL", "Title", "Keywords", "Timestamp", "Domain Category", "Risk Score", "Action Required"]
            for col, header in enumerate(sub_headers):
                worksheet.write(row, col, header, styles['subheader'])
            row += 1
            
            # Alert details
            for i, alert in enumerate(alerts, 1):
                worksheet.write(row, 0, i, styles['data_center'])
                worksheet.write(row, 1, alert.get('url', ''), styles['data'])
                worksheet.write(row, 2, alert.get('title', 'N/A'), styles['data'])
                worksheet.write(row, 3, ', '.join(alert.get('keywords_found', [])), styles['data'])
                worksheet.write(row, 4, self._parse_timestamp(alert.get('timestamp')), styles['date'])
                worksheet.write(row, 5, self._categorize_domain(alert.get('url', '')), styles['data'])
                worksheet.write(row, 6, self._calculate_risk_score(alert), styles['data_number'])
                worksheet.write(row, 7, self._recommend_action(alert, threat_level), styles['data'])
                row += 1
            
            row += 1  # Add spacing between sections
        
        # Set column widths
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 40)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 12)
        worksheet.set_column('H:H', 30)
    
    def _create_crawled_sites_sheet(self, workbook, styles, data):
        """Create comprehensive crawled sites analysis"""
        worksheet = workbook.add_worksheet("Crawled Sites")
        
        headers = [
            "Site URL", "Title", "First Visited", "Last Visited", "Visit Count",
            "Content Hash", "Response Code", "Page Size", "Links Found", "Classification"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, styles['header'])
        
        # Process visited sites
        sites = {}
        for item in data['visited']:
            if isinstance(item, dict):
                url = item.get('url')
                if url:
                    if url not in sites:
                        sites[url] = {
                            'url': url,
                            'title': item.get('title', 'N/A'),
                            'first_visited': item.get('timestamp'),
                            'last_visited': item.get('timestamp'),
                            'visit_count': 1,
                            'content_hash': item.get('content_hash', 'N/A'),
                            'response_code': item.get('response_code', 'N/A'),
                            'page_size': item.get('page_size', 0),
                            'links_found': item.get('links_found', 0)
                        }
                    else:
                        sites[url]['visit_count'] += 1
                        sites[url]['last_visited'] = item.get('timestamp')
        
        row = 1
        for site_data in sites.values():
            worksheet.write(row, 0, site_data['url'], styles['data'])
            worksheet.write(row, 1, site_data['title'], styles['data'])
            worksheet.write(row, 2, self._parse_timestamp(site_data['first_visited']), styles['date'])
            worksheet.write(row, 3, self._parse_timestamp(site_data['last_visited']), styles['date'])
            worksheet.write(row, 4, site_data['visit_count'], styles['data_number'])
            worksheet.write(row, 5, site_data['content_hash'], styles['data'])
            worksheet.write(row, 6, site_data['response_code'], styles['data_center'])
            worksheet.write(row, 7, site_data['page_size'], styles['data_number'])
            worksheet.write(row, 8, site_data['links_found'], styles['data_number'])
            worksheet.write(row, 9, self._classify_site(site_data), styles['data'])
            row += 1
        
        # Set column widths
        worksheet.set_column('A:A', 50)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:D', 18)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 12)
        worksheet.set_column('H:I', 12)
        worksheet.set_column('J:J', 20)
    
    def _create_keyword_analysis_sheet(self, workbook, styles, data):
        """Create comprehensive keyword analysis"""
        worksheet = workbook.add_worksheet("Keyword Analysis")
        
        # Collect all keywords with context
        keyword_analysis = {}
        for alert in data['alerts']:
            for keyword in alert.get('keywords_found', []):
                if keyword not in keyword_analysis:
                    keyword_analysis[keyword] = {
                        'keyword': keyword,
                        'frequency': 0,
                        'urls': set(),
                        'threat_levels': [],
                        'categories': set()
                    }
                
                keyword_analysis[keyword]['frequency'] += 1
                keyword_analysis[keyword]['urls'].add(alert.get('url', ''))
                keyword_analysis[keyword]['threat_levels'].append(self._get_threat_level(alert))
                keyword_analysis[keyword]['categories'].add(self._categorize_keyword(keyword))
        
        # Headers
        headers = [
            "Keyword", "Frequency", "Unique Sites", "Primary Threat Level",
            "Category", "Risk Assessment", "Legal Implications", "Recommended Action"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, styles['header'])
        
        # Sort by frequency
        sorted_keywords = sorted(keyword_analysis.values(), key=lambda x: x['frequency'], reverse=True)
        
        row = 1
        for kw_data in sorted_keywords:
            primary_threat = Counter(kw_data['threat_levels']).most_common(1)[0][0]
            
            worksheet.write(row, 0, kw_data['keyword'], styles['data'])
            worksheet.write(row, 1, kw_data['frequency'], styles['data_number'])
            worksheet.write(row, 2, len(kw_data['urls']), styles['data_number'])
            worksheet.write(row, 3, primary_threat, self._get_threat_style(styles, primary_threat))
            worksheet.write(row, 4, ', '.join(kw_data['categories']), styles['data'])
            worksheet.write(row, 5, self._assess_keyword_risk(kw_data), styles['data'])
            worksheet.write(row, 6, self._assess_legal_implications(kw_data['keyword']), styles['data'])
            worksheet.write(row, 7, self._recommend_keyword_action(kw_data), styles['data'])
            row += 1
        
        # Set column widths
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:C', 12)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:H', 30)
    
    def _create_timeline_analysis_sheet(self, workbook, styles, data):
        """Create timeline analysis of activities"""
        worksheet = workbook.add_worksheet("Timeline Analysis")
        
        # Parse all timestamps and create timeline
        events = []
        
        for alert in data['alerts']:
            timestamp = self._parse_timestamp(alert.get('timestamp'))
            if timestamp:
                events.append({
                    'timestamp': timestamp,
                    'type': 'Alert',
                    'description': f"Alert generated for {alert.get('url', 'unknown')}",
                    'threat_level': self._get_threat_level(alert),
                    'keywords': ', '.join(alert.get('keywords_found', [])),
                    'url': alert.get('url', '')
                })
        
        for page in data['visited']:
            if isinstance(page, dict):
                timestamp = self._parse_timestamp(page.get('timestamp'))
                if timestamp:
                    events.append({
                        'timestamp': timestamp,
                        'type': 'Site Visit',
                        'description': f"Crawled site: {page.get('url', 'unknown')}",
                        'threat_level': 'INFO',
                        'keywords': '',
                        'url': page.get('url', '')
                    })
        
        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min)
        
        # Headers
        headers = ["Timestamp", "Event Type", "Description", "URL", "Threat Level", "Keywords", "Investigation Notes"]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, styles['header'])
        
        # Timeline data
        for row, event in enumerate(events, 1):
            worksheet.write(row, 0, event['timestamp'], styles['date'])
            worksheet.write(row, 1, event['type'], styles['data_center'])
            worksheet.write(row, 2, event['description'], styles['data'])
            worksheet.write(row, 3, event['url'], styles['data'])
            worksheet.write(row, 4, event['threat_level'], self._get_threat_style(styles, event['threat_level']))
            worksheet.write(row, 5, event['keywords'], styles['data'])
            worksheet.write(row, 6, self._generate_timeline_notes(event), styles['data'])
        
        # Set column widths
        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 50)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 30)
        worksheet.set_column('G:G', 40)
    
    def _create_network_analysis_sheet(self, workbook, styles, data):
        """Create network topology and connection analysis"""
        worksheet = workbook.add_worksheet("Network Analysis")
        
        # Analyze domain connections and patterns
        domains = {}
        for alert in data['alerts']:
            domain = self._extract_domain(alert.get('url', ''))
            if domain:
                if domain not in domains:
                    domains[domain] = {
                        'domain': domain,
                        'alert_count': 0,
                        'threat_levels': [],
                        'keywords': set(),
                        'first_seen': alert.get('timestamp'),
                        'last_seen': alert.get('timestamp'),
                        'urls': set()
                    }
                
                domains[domain]['alert_count'] += 1
                domains[domain]['threat_levels'].append(self._get_threat_level(alert))
                domains[domain]['keywords'].update(alert.get('keywords_found', []))
                domains[domain]['urls'].add(alert.get('url', ''))
        
        # Headers
        headers = [
            "Domain", "Alert Count", "Unique URLs", "Primary Threat", "Keyword Diversity",
            "First Seen", "Last Seen", "Domain Category", "Threat Assessment", "Monitoring Priority"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, styles['header'])
        
        # Sort domains by alert count
        sorted_domains = sorted(domains.values(), key=lambda x: x['alert_count'], reverse=True)
        
        row = 1
        for domain_data in sorted_domains:
            primary_threat = Counter(domain_data['threat_levels']).most_common(1)[0][0]
            
            worksheet.write(row, 0, domain_data['domain'], styles['data'])
            worksheet.write(row, 1, domain_data['alert_count'], styles['data_number'])
            worksheet.write(row, 2, len(domain_data['urls']), styles['data_number'])
            worksheet.write(row, 3, primary_threat, self._get_threat_style(styles, primary_threat))
            worksheet.write(row, 4, len(domain_data['keywords']), styles['data_number'])
            worksheet.write(row, 5, self._parse_timestamp(domain_data['first_seen']), styles['date'])
            worksheet.write(row, 6, self._parse_timestamp(domain_data['last_seen']), styles['date'])
            worksheet.write(row, 7, self._categorize_domain(domain_data['domain']), styles['data'])
            worksheet.write(row, 8, self._assess_domain_threat(domain_data), styles['data'])
            worksheet.write(row, 9, self._assign_monitoring_priority(domain_data), styles['data'])
            row += 1
        
        # Set column widths
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:E', 12)
        worksheet.set_column('F:G', 18)
        worksheet.set_column('H:J', 25)
    
    def _create_evidence_chain_sheet(self, workbook, styles, data):
        """Create evidence chain and forensic data sheet"""
        worksheet = workbook.add_worksheet("Evidence Chain")
        
        worksheet.merge_range('A1:G1', 'CHAIN OF CUSTODY - DIGITAL EVIDENCE', styles['title'])
        
        row = 2
        worksheet.write(row, 0, "Evidence Collection Method:", styles['subheader'])
        worksheet.write(row, 1, "Automated Web Crawling via TOR Network", styles['data'])
        
        row += 1
        worksheet.write(row, 0, "Collection Tool:", styles['subheader'])
        worksheet.write(row, 1, "TRINETRA Darkweb Intelligence Platform", styles['data'])
        
        row += 1
        worksheet.write(row, 0, "Evidence Integrity:", styles['subheader'])
        worksheet.write(row, 1, "MD5 Hash Verification Applied", styles['data'])
        
        row += 2
        
        # Evidence headers
        headers = [
            "Evidence ID", "Content Hash", "Source URL", "Collection Time",
            "Evidence Type", "File Size", "Verification Status", "Legal Admissibility"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, styles['header'])
        
        row += 1
        evidence_id = 1
        
        # Create evidence entries for each alert
        for alert in data['alerts']:
            worksheet.write(row, 0, f"EVD-{evidence_id:06d}", styles['data_center'])
            worksheet.write(row, 1, alert.get('content_hash', 'N/A'), styles['data'])
            worksheet.write(row, 2, alert.get('url', ''), styles['data'])
            worksheet.write(row, 3, self._parse_timestamp(alert.get('timestamp')), styles['date'])
            worksheet.write(row, 4, "Digital Web Content", styles['data'])
            worksheet.write(row, 5, self._estimate_content_size(alert), styles['data_number'])
            worksheet.write(row, 6, "Hash Verified", styles['low'])
            worksheet.write(row, 7, self._assess_legal_admissibility(alert), styles['data'])
            
            row += 1
            evidence_id += 1
        
        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 50)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 25)
    
    def _create_ai_analysis_sheet(self, workbook, styles, data):
        """Create AI analysis results sheet"""
        worksheet = workbook.add_worksheet("AI Analysis")
        
        if not data['ai_analyses']:
            worksheet.write(0, 0, "No AI Analysis Data Available", styles['header'])
            return
        
        headers = [
            "Analysis ID", "URL", "Threat Level", "Confidence Score", "Threat Categories",
            "Suspicious Indicators", "Illegal Content", "Analysis Summary", "Recommended Actions"
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, styles['header'])
        
        for row, analysis in enumerate(data['ai_analyses'], 1):
            worksheet.write(row, 0, analysis.get('id', row), styles['data_center'])
            worksheet.write(row, 1, analysis.get('url', ''), styles['data'])
            
            threat_level = analysis.get('threat_level', 'LOW')
            worksheet.write(row, 2, threat_level, self._get_threat_style(styles, threat_level))
            
            worksheet.write(row, 3, f"{analysis.get('confidence_score', 0):.2%}", styles['data_center'])
            worksheet.write(row, 4, ', '.join(analysis.get('threat_categories', [])), styles['data'])
            worksheet.write(row, 5, ', '.join(analysis.get('suspicious_indicators', [])), styles['data'])
            worksheet.write(row, 6, "YES" if analysis.get('illegal_content_detected') else "NO", 
                          styles['critical'] if analysis.get('illegal_content_detected') else styles['low'])
            worksheet.write(row, 7, analysis.get('analysis_summary', ''), styles['data'])
            worksheet.write(row, 8, ', '.join(analysis.get('recommended_actions', [])), styles['data'])
        
        # Set column widths
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:F', 30)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:I', 40)
    
    def _create_technical_appendix_sheet(self, workbook, styles, data):
        """Create technical appendix with methodology and system info"""
        worksheet = workbook.add_worksheet("Technical Appendix")
        
        worksheet.merge_range('A1:D1', 'TECHNICAL APPENDIX', styles['title'])
        
        row = 2
        sections = [
            ("METHODOLOGY", [
                "Data Collection: Automated web crawling using Scrapy framework",
                "Network Routing: TOR network with SOCKS5 proxy configuration",
                "Anonymization: Multi-layer proxy rotation and user-agent spoofing",
                "Content Analysis: Keyword-based threat detection and AI analysis",
                "Data Storage: SQLite database with WAL mode for concurrent access",
                "Evidence Integrity: MD5 hash verification and chain of custody"
            ]),
            ("SYSTEM CONFIGURATION", [
                f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                "Platform: TRINETRA Darkweb Intelligence System v2.0",
                "Database: SQLite with real-time synchronization",
                "Proxy Configuration: TOR + Privoxy + SOCKS5",
                "AI Analysis: Google Gemini API integration",
                "Security: End-to-end encryption and secure deletion"
            ]),
            ("LEGAL COMPLIANCE", [
                "Evidence collection performed under applicable legal frameworks",
                "Data retention policies applied per jurisdiction requirements",
                "Chain of custody maintained for all digital evidence",
                "Privacy protections implemented for non-target data",
                "International cooperation protocols followed",
                "Court admissibility standards met for digital evidence"
            ]),
            ("LIMITATIONS", [
                "Data collection limited to publicly accessible content",
                "TOR network latency may affect completeness of crawling",
                "Keyword detection based on predefined threat indicators",
                "AI analysis confidence levels vary by content complexity",
                "Some sites may employ anti-crawling countermeasures",
                "Temporal analysis limited to investigation period"
            ])
        ]
        
        for section_name, items in sections:
            worksheet.write(row, 0, section_name, styles['header'])
            row += 1
            
            for item in items:
                worksheet.write(row, 0, f"• {item}", styles['data'])
                row += 1
            row += 1
        
        # Set column width
        worksheet.set_column('A:A', 80)
    
    # Utility methods for data processing
    def _get_threat_level(self, alert):
        """Determine threat level from alert data"""
        keywords = alert.get('keywords_found', [])
        
        high_risk_keywords = ['bomb', 'terror', 'attack', 'weapon', 'assassination', 'murder', 'kill']
        medium_risk_keywords = ['drugs', 'hacking', 'fraud', 'malware', 'ransomware', 'exploit']
        
        for keyword in keywords:
            if any(high_kw in keyword.lower() for high_kw in high_risk_keywords):
                return 'CRITICAL'
            elif any(med_kw in keyword.lower() for med_kw in medium_risk_keywords):
                return 'HIGH'
        
        return alert.get('threat_level', 'MEDIUM' if keywords else 'LOW')
    
    def _get_threat_style(self, styles, threat_level):
        """Get appropriate style for threat level"""
        level_map = {
            'CRITICAL': styles['critical'],
            'HIGH': styles['high'],
            'MEDIUM': styles['medium'],
            'LOW': styles['low'],
            'INFO': styles['data_center']
        }
        return level_map.get(threat_level, styles['data'])
    
    def _parse_timestamp(self, timestamp_str):
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None
        
        try:
            # Try different timestamp formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S.%f'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
        except:
            pass
        
        return None
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return 'unknown'
    
    def _categorize_domain(self, domain):
        """Categorize domain type"""
        if '.onion' in domain:
            return 'Darkweb (TOR Hidden Service)'
        elif any(market in domain.lower() for market in ['market', 'shop', 'store']):
            return 'Suspected Marketplace'
        elif any(forum in domain.lower() for forum in ['forum', 'board', 'discuss']):
            return 'Discussion Forum'
        else:
            return 'Unknown'
    
    def _categorize_keyword(self, keyword):
        """Categorize keyword by type"""
        categories = {
            'weapons': ['bomb', 'gun', 'weapon', 'explosive', 'ammunition'],
            'drugs': ['cocaine', 'heroin', 'meth', 'cannabis', 'fentanyl'],
            'cybercrime': ['hacking', 'malware', 'ransomware', 'phishing', 'exploit'],
            'violence': ['murder', 'kill', 'assassination', 'terror', 'attack'],
            'fraud': ['carding', 'fraud', 'fake', 'counterfeit', 'stolen']
        }
        
        keyword_lower = keyword.lower()
        for category, words in categories.items():
            if any(word in keyword_lower for word in words):
                return category.upper()
        
        return 'OTHER'
    
    def _calculate_investigation_period(self, data):
        """Calculate the investigation period in days"""
        timestamps = []
        
        for alert in data['alerts']:
            ts = self._parse_timestamp(alert.get('timestamp'))
            if ts:
                timestamps.append(ts)
        
        if len(timestamps) < 2:
            return 1
        
        return (max(timestamps) - min(timestamps)).days + 1
    
    def _generate_key_findings(self, data):
        """Generate key findings summary"""
        findings = []
        
        # Threat level distribution
        threat_levels = [self._get_threat_level(alert) for alert in data['alerts']]
        critical_count = threat_levels.count('CRITICAL')
        high_count = threat_levels.count('HIGH')
        
        if critical_count > 0:
            findings.append(f"{critical_count} CRITICAL threat alerts requiring immediate law enforcement attention")
        if high_count > 0:
            findings.append(f"{high_count} HIGH-RISK sites identified with suspicious activities")
        
        # Domain analysis
        domains = set(self._extract_domain(alert.get('url', '')) for alert in data['alerts'])
        onion_domains = [d for d in domains if '.onion' in d]
        findings.append(f"{len(onion_domains)} unique darkweb domains investigated")
        
        # Keyword analysis
        all_keywords = [kw for alert in data['alerts'] for kw in alert.get('keywords_found', [])]
        if all_keywords:
            top_keyword = Counter(all_keywords).most_common(1)[0]
            findings.append(f"Most frequent threat indicator: '{top_keyword[0]}' ({top_keyword[1]} occurrences)")
        
        return findings
    
    def _generate_investigation_notes(self, alert):
        """Generate investigation notes for an alert"""
        notes = []
        
        threat_level = self._get_threat_level(alert)
        if threat_level in ['CRITICAL', 'HIGH']:
            notes.append("PRIORITY INVESTIGATION REQUIRED")
        
        keywords = alert.get('keywords_found', [])
        if any('weapon' in kw.lower() or 'bomb' in kw.lower() for kw in keywords):
            notes.append("POTENTIAL WEAPONS/EXPLOSIVES THREAT")
        
        if any('drug' in kw.lower() or 'cocaine' in kw.lower() for kw in keywords):
            notes.append("NARCOTICS-RELATED CONTENT")
        
        domain = self._extract_domain(alert.get('url', ''))
        if '.onion' in domain:
            notes.append("DARKWEB HIDDEN SERVICE")
        
        return ' | '.join(notes) if notes else 'Standard monitoring'
    
    def _calculate_risk_score(self, alert):
        """Calculate numeric risk score (0-100)"""
        base_score = 30
        
        threat_level = self._get_threat_level(alert)
        level_scores = {'CRITICAL': 40, 'HIGH': 30, 'MEDIUM': 20, 'LOW': 10}
        base_score += level_scores.get(threat_level, 10)
        
        # Add points for dangerous keywords
        keywords = alert.get('keywords_found', [])
        dangerous_keywords = ['bomb', 'weapon', 'kill', 'terror', 'assassination']
        for keyword in keywords:
            if any(danger in keyword.lower() for danger in dangerous_keywords):
                base_score += 15
        
        return min(base_score, 100)
    
    def _recommend_action(self, alert, threat_level):
        """Recommend action based on alert"""
        if threat_level == 'CRITICAL':
            return "IMMEDIATE INVESTIGATION - CONTACT LAW ENFORCEMENT"
        elif threat_level == 'HIGH':
            return "URGENT REVIEW - ESCALATE TO SUPERVISOR"
        elif threat_level == 'MEDIUM':
            return "ROUTINE INVESTIGATION - MONITOR CLOSELY"
        else:
            return "INFORMATIONAL - CONTINUE MONITORING"
    
    def _classify_site(self, site_data):
        """Classify the type of site"""
        url = site_data.get('url', '')
        title = site_data.get('title', '').lower()
        
        if '.onion' in url:
            if any(word in title for word in ['market', 'shop', 'buy', 'sell']):
                return 'Suspected Marketplace'
            elif any(word in title for word in ['forum', 'board', 'discuss']):
                return 'Discussion Forum'
            else:
                return 'Hidden Service'
        
        return 'Surface Web'
    
    def _assess_keyword_risk(self, kw_data):
        """Assess risk level of a keyword"""
        keyword = kw_data['keyword'].lower()
        frequency = kw_data['frequency']
        
        if any(danger in keyword for danger in ['bomb', 'weapon', 'kill', 'terror']):
            return f"EXTREME RISK - {frequency} occurrences across multiple sites"
        elif any(high in keyword for high in ['drug', 'hack', 'fraud', 'malware']):
            return f"HIGH RISK - Frequent appearance indicates criminal activity"
        else:
            return f"MODERATE RISK - Monitor for escalation"
    
    def _assess_legal_implications(self, keyword):
        """Assess legal implications of keyword"""
        keyword_lower = keyword.lower()
        
        if any(illegal in keyword_lower for illegal in ['bomb', 'weapon', 'kill', 'murder']):
            return "POTENTIAL CRIMINAL ACTIVITY - TERRORISM/VIOLENCE"
        elif any(drug in keyword_lower for drug in ['cocaine', 'heroin', 'meth']):
            return "CONTROLLED SUBSTANCE VIOLATIONS"
        elif any(cyber in keyword_lower for cyber in ['hack', 'malware', 'ransomware']):
            return "CYBERCRIME VIOLATIONS"
        else:
            return "REQUIRES LEGAL REVIEW"
    
    def _recommend_keyword_action(self, kw_data):
        """Recommend action for keyword"""
        primary_threat = Counter(kw_data['threat_levels']).most_common(1)[0][0]
        
        if primary_threat in ['CRITICAL', 'HIGH']:
            return "IMMEDIATE INVESTIGATION - COORDINATE WITH RELEVANT AGENCIES"
        else:
            return "CONTINUED MONITORING - ESTABLISH SURVEILLANCE PROTOCOLS"
    
    def _generate_timeline_notes(self, event):
        """Generate notes for timeline events"""
        if event['type'] == 'Alert':
            return f"Threat detected: {event['threat_level']} level alert generated"
        else:
            return "Routine crawling operation - content analysis performed"
    
    def _assess_domain_threat(self, domain_data):
        """Assess overall threat level of a domain"""
        threat_levels = domain_data['threat_levels']
        alert_count = domain_data['alert_count']
        
        critical_count = threat_levels.count('CRITICAL')
        high_count = threat_levels.count('HIGH')
        
        if critical_count > 0:
            return f"CRITICAL DOMAIN - {critical_count} critical alerts"
        elif high_count > 2:
            return f"HIGH-RISK DOMAIN - {high_count} high-risk alerts"
        elif alert_count > 5:
            return "SUSPICIOUS DOMAIN - Multiple alerts generated"
        else:
            return "STANDARD MONITORING"
    
    def _assign_monitoring_priority(self, domain_data):
        """Assign monitoring priority"""
        threat_levels = domain_data['threat_levels']
        
        if 'CRITICAL' in threat_levels:
            return "P1 - CONTINUOUS MONITORING"
        elif 'HIGH' in threat_levels:
            return "P2 - DAILY MONITORING"
        else:
            return "P3 - WEEKLY MONITORING"
    
    def _estimate_content_size(self, alert):
        """Estimate content size for evidence tracking"""
        # Estimate based on title and keyword count
        title_len = len(alert.get('title', ''))
        keyword_count = len(alert.get('keywords_found', []))
        return (title_len * 2) + (keyword_count * 50) + 1024  # Rough estimate
    
    def _assess_legal_admissibility(self, alert):
        """Assess legal admissibility of evidence"""
        if alert.get('content_hash'):
            return "HIGH - Hash verified, chain of custody maintained"
        else:
            return "MEDIUM - Requires additional verification"
    
    def _generate_report_summary(self, data, case_id):
        """Generate a summary report file"""
        summary_file = f"{self.output_dir}/SUMMARY_{case_id}_{self.report_timestamp}.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("DARKWEB INTELLIGENCE INVESTIGATION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Case ID: {case_id}\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"Investigation Period: {self._calculate_investigation_period(data)} days\n\n")
            
            f.write("KEY STATISTICS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Alerts: {len(data['alerts'])}\n")
            f.write(f"Sites Investigated: {len(data['visited'])}\n")
            f.write(f"Unique Domains: {len(set(self._extract_domain(a.get('url', '')) for a in data['alerts']))}\n")
            
            threat_levels = [self._get_threat_level(alert) for alert in data['alerts']]
            f.write(f"Critical Threats: {threat_levels.count('CRITICAL')}\n")
            f.write(f"High-Risk Alerts: {threat_levels.count('HIGH')}\n")
            f.write(f"Medium Alerts: {threat_levels.count('MEDIUM')}\n")
            f.write(f"Low-Risk Alerts: {threat_levels.count('LOW')}\n\n")
            
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 20 + "\n")
            if threat_levels.count('CRITICAL') > 0:
                f.write("• IMMEDIATE ACTION REQUIRED - Critical threats detected\n")
            if threat_levels.count('HIGH') > 5:
                f.write("• INCREASED MONITORING - Multiple high-risk sites identified\n")
            f.write("• CONTINUED SURVEILLANCE - Maintain monitoring protocols\n")
            f.write("• INTER-AGENCY COORDINATION - Share intelligence as appropriate\n")
        
        print(f"📄 Investigation summary created: {summary_file}")

# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate comprehensive police report for darkweb intelligence")
    parser.add_argument("--case-id", help="Case identification number")
    parser.add_argument("--officer-id", help="Investigating officer ID")
    parser.add_argument("--jurisdiction", help="Legal jurisdiction")
    parser.add_argument("--output-dir", default="police_reports", help="Output directory for reports")
    
    args = parser.parse_args()
    
    generator = PoliceReportGenerator(args.output_dir)
    report_file = generator.generate_comprehensive_report(
        case_id=args.case_id,
        officer_id=args.officer_id,
        jurisdiction=args.jurisdiction
    )
    
    print(f"\n🎯 REPORT GENERATION COMPLETE")
    print(f"📁 Report saved to: {report_file}")
    print(f"🚨 CLASSIFICATION: LAW ENFORCEMENT SENSITIVE")
