"""
TRINETRA 3.0 - Gemini AI Integration Module
Military-Grade AI-Powered Threat Analysis and Intelligence Processing
"""

import google.generativeai as genai
import json
import logging
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
import time
import requests
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ThreatAnalysis:
    """Threat analysis result from Gemini AI"""
    content_hash: str
    threat_level: str  # CRITICAL, HIGH, MEDIUM, LOW, BENIGN
    threat_categories: List[str]
    suspicious_indicators: List[str]
    illegal_content_detected: bool
    confidence_score: float
    analysis_summary: str
    recommended_actions: List[str]
    ai_reasoning: str
    timestamp: str

class GeminiThreatAnalyzer:
    """Advanced AI-powered threat analysis using Google Gemini"""
    
    def __init__(self, api_key: str = "AIzaSyAoCdXfVSF5pWNkaDoDUWPo_491HLK3OWk"):
        """Initialize Gemini AI analyzer"""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
        logger.info("🧠 Gemini AI Threat Analyzer initialized")
        
        # Threat detection prompt templates
        self.threat_analysis_prompt = """
        You are TRINETRA AI, a military-grade threat intelligence analyst specializing in darknet content analysis.
        Analyze the following content for illegal activities, threats, and suspicious behavior.

        CRITICAL ANALYSIS REQUIREMENTS:
        1. Identify illegal activities (drugs, weapons, terrorism, child exploitation, human trafficking, etc.)
        2. Detect cybercrime indicators (malware, phishing, carding, hacking services, etc.)
        3. Assess threat level against national security
        4. Identify suspicious communication patterns
        5. Flag potential terrorist or extremist content
        6. Detect money laundering or financial crimes
        7. Detect social engineering attempts (phishing, scams, manipulation tactics)
        8. Identify disinformation campaigns and propaganda

        Content to analyze:
        URL: {url}
        Title: {title}
        Content: {content}
        Keywords Found: {keywords}

        Respond in JSON format:
        {{
            "threat_level": "CRITICAL|HIGH|MEDIUM|LOW|BENIGN",
            "threat_categories": ["category1", "category2"],
            "suspicious_indicators": ["indicator1", "indicator2"],
            "illegal_content_detected": true/false,
            "confidence_score": 0.0-1.0,
            "analysis_summary": "Brief summary of findings",
            "recommended_actions": ["action1", "action2"],
            "ai_reasoning": "Detailed reasoning for the assessment"
        }}
        
        Be thorough, accurate, and prioritize public safety.
        """

    async def analyze_content(self, 
                            url: str, 
                            title: str, 
                            content: str, 
                            keywords: List[str]) -> Optional[ThreatAnalysis]:
        """Analyze content using Gemini AI for threat detection"""
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - (current_time - self.last_request_time))
            
            self.last_request_time = time.time()
            
            # Truncate content if too long
            content_sample = content[:4000] if len(content) > 4000 else content
            
            # Format the prompt
            prompt = self.threat_analysis_prompt.format(
                url=url,
                title=title,
                content=content_sample,
                keywords=', '.join(keywords)
            )
            
            # Generate AI analysis
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                logger.warning(f"Empty response from Gemini for {url}")
                return None
                
            # Parse JSON response
            try:
                analysis_data = json.loads(response.text.strip())
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from response
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    analysis_data = json.loads(json_match.group())
                else:
                    logger.error(f"Failed to parse JSON from Gemini response: {response.text}")
                    return None
            
            # Create threat analysis object
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            analysis = ThreatAnalysis(
                content_hash=content_hash,
                threat_level=analysis_data.get('threat_level', 'LOW'),
                threat_categories=analysis_data.get('threat_categories', []),
                suspicious_indicators=analysis_data.get('suspicious_indicators', []),
                illegal_content_detected=analysis_data.get('illegal_content_detected', False),
                confidence_score=float(analysis_data.get('confidence_score', 0.0)),
                analysis_summary=analysis_data.get('analysis_summary', ''),
                recommended_actions=analysis_data.get('recommended_actions', []),
                ai_reasoning=analysis_data.get('ai_reasoning', ''),
                timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"🎯 AI Analysis completed for {url}: {analysis.threat_level} threat level")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing content with Gemini AI: {e}")
            return None

    def analyze_content_sync(self, url: str, title: str, content: str, keywords: List[str]) -> Optional[ThreatAnalysis]:
        """Synchronous wrapper for content analysis"""
        try:
            return asyncio.run(self.analyze_content(url, title, content, keywords))
        except Exception as e:
            logger.error(f"Error in sync analysis: {e}")
            return None

    async def batch_analyze(self, content_batch: List[Dict]) -> List[ThreatAnalysis]:
        """Analyze multiple content items in batch"""
        results = []
        
        for item in content_batch:
            analysis = await self.analyze_content(
                item.get('url', ''),
                item.get('title', ''),
                item.get('content', ''),
                item.get('keywords', [])
            )
            
            if analysis:
                results.append(analysis)
                
            # Respect rate limits
            await asyncio.sleep(1.2)
        
        return results

    def generate_intelligence_report(self, analyses: List[ThreatAnalysis]) -> Dict:
        """Generate comprehensive intelligence report from analyses"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_items_analyzed": len(analyses),
            "threat_summary": {
                "critical_threats": 0,
                "high_threats": 0,
                "medium_threats": 0,
                "low_threats": 0,
                "benign_content": 0
            },
            "illegal_content_count": 0,
            "top_threat_categories": {},
            "top_suspicious_indicators": {},
            "high_confidence_threats": [],
            "recommended_immediate_actions": []
        }
        
        # Process analyses
        for analysis in analyses:
            # Count threat levels
            threat_level = analysis.threat_level.lower()
            if threat_level == 'critical':
                report["threat_summary"]["critical_threats"] += 1
            elif threat_level == 'high':
                report["threat_summary"]["high_threats"] += 1
            elif threat_level == 'medium':
                report["threat_summary"]["medium_threats"] += 1
            elif threat_level == 'low':
                report["threat_summary"]["low_threats"] += 1
            else:
                report["threat_summary"]["benign_content"] += 1
            
            # Count illegal content
            if analysis.illegal_content_detected:
                report["illegal_content_count"] += 1
            
            # Aggregate threat categories
            for category in analysis.threat_categories:
                report["top_threat_categories"][category] = report["top_threat_categories"].get(category, 0) + 1
            
            # Aggregate suspicious indicators
            for indicator in analysis.suspicious_indicators:
                report["top_suspicious_indicators"][indicator] = report["top_suspicious_indicators"].get(indicator, 0) + 1
            
            # High confidence threats
            if analysis.confidence_score > 0.8 and analysis.threat_level in ['CRITICAL', 'HIGH']:
                report["high_confidence_threats"].append({
                    "content_hash": analysis.content_hash,
                    "threat_level": analysis.threat_level,
                    "confidence": analysis.confidence_score,
                    "summary": analysis.analysis_summary,
                    "timestamp": analysis.timestamp
                })
            
            # Immediate actions
            if analysis.threat_level in ['CRITICAL', 'HIGH']:
                report["recommended_immediate_actions"].extend(analysis.recommended_actions)
        
        # Sort and limit results
        report["top_threat_categories"] = dict(sorted(report["top_threat_categories"].items(), key=lambda x: x[1], reverse=True)[:10])
        report["top_suspicious_indicators"] = dict(sorted(report["top_suspicious_indicators"].items(), key=lambda x: x[1], reverse=True)[:10])
        report["recommended_immediate_actions"] = list(set(report["recommended_immediate_actions"]))[:10]
        
        return report

    def analyze_url_structure(self, url: str) -> Dict:
        """Analyze URL structure for suspicious patterns"""
        try:
            parsed = urlparse(url)
            
            # Suspicious URL patterns
            suspicious_patterns = [
                r'(?i)(admin|login|panel|cp|dashboard)',
                r'(?i)(upload|shell|cmd|exec)',
                r'(?i)(hack|crack|exploit|vuln)',
                r'(?i)(drug|weapon|bomb|terror)',
                r'(?i)(card|cc|cvv|dump|fullz)',
                r'(?i)(bitcoin|btc|monero|crypto)',
                r'(?i)(porn|xxx|sex|escort)',
                r'(?i)(market|shop|store|buy)',
                r'[0-9a-f]{16,}',  # Long hex strings
                r'[a-z]{20,}'      # Long random strings
            ]
            
            analysis = {
                "is_onion": parsed.hostname and parsed.hostname.endswith('.onion'),
                "suspicious_path": any(re.search(pattern, parsed.path) for pattern in suspicious_patterns),
                "suspicious_query": any(re.search(pattern, parsed.query) for pattern in suspicious_patterns) if parsed.query else False,
                "deep_level": parsed.path.count('/') > 3,
                "has_parameters": bool(parsed.query),
                "risk_score": 0
            }
            
            # Calculate risk score
            if analysis["is_onion"]:
                analysis["risk_score"] += 3
            if analysis["suspicious_path"]:
                analysis["risk_score"] += 4
            if analysis["suspicious_query"]:
                analysis["risk_score"] += 2
            if analysis["deep_level"]:
                analysis["risk_score"] += 1
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing URL structure: {e}")
            return {"error": str(e)}

    def create_threat_signature(self, analysis: ThreatAnalysis) -> str:
        """Create unique threat signature for tracking"""
        signature_data = f"{analysis.threat_level}_{','.join(analysis.threat_categories)}_{analysis.confidence_score}"
        return hashlib.sha256(signature_data.encode()).hexdigest()[:16]

# Global analyzer instance
gemini_analyzer = GeminiThreatAnalyzer()

async def analyze_with_ai(url: str, title: str, content: str, keywords: List[str]) -> Optional[ThreatAnalysis]:
    """Convenience function for AI analysis"""
    return await gemini_analyzer.analyze_content(url, title, content, keywords)

def analyze_with_ai_sync(url: str, title: str, content: str, keywords: List[str]) -> Optional[ThreatAnalysis]:
    """Synchronous convenience function for AI analysis"""
    return gemini_analyzer.analyze_content_sync(url, title, content, keywords)
