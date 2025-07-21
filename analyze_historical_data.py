#!/usr/bin/env python3
"""
TRINETRA 3.0 - Historical Data AI Analysis Script
Analyzes past crawled data with AI to populate the AI analysis database
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.gemini_analyzer import gemini_analyzer, ThreatAnalysis
from database.models import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_historical_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HistoricalDataAnalyzer:
    """Analyze historical crawled data with AI"""
    
    def __init__(self, batch_size: int = 5):
        self.batch_size = batch_size
        self.db = db_manager
        self.analyzer = gemini_analyzer
        self.processed_count = 0
        self.failed_count = 0
        self.success_count = 0
        
    def get_historical_data(self, limit: int = None) -> List[Dict]:
        """Get historical data that hasn't been analyzed by AI yet"""
        try:
            with self.db.get_cursor() as cursor:
                # Get alerts that haven't been analyzed by AI yet
                query = """
                    SELECT DISTINCT a.url, a.title, a.keywords_found, a.content_hash
                    FROM alerts a
                    LEFT JOIN ai_analysis ai ON a.content_hash = ai.content_hash
                    WHERE ai.content_hash IS NULL
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                historical_data = []
                for row in rows:
                    try:
                        keywords = json.loads(row['keywords_found']) if row['keywords_found'] else []
                    except json.JSONDecodeError:
                        keywords = []
                    
                    historical_data.append({
                        'url': row['url'],
                        'title': row['title'] or '',
                        'content': '',  # We'll use title + url as content for historical data
                        'keywords': keywords,
                        'content_hash': row['content_hash']
                    })
                
                logger.info(f"📊 Found {len(historical_data)} historical records to analyze")
                return historical_data
                
        except Exception as e:
            logger.error(f"❌ Error retrieving historical data: {e}")
            return []
    
    async def analyze_batch(self, batch: List[Dict]) -> List[ThreatAnalysis]:
        """Analyze a batch of historical data"""
        results = []
        
        for item in batch:
            try:
                logger.info(f"🔍 Analyzing: {item['url']}")
                
                # For historical data, we'll analyze based on URL, title, and found keywords
                content_for_analysis = f"Title: {item['title']}\nKeywords Found: {', '.join(item['keywords'])}"
                
                analysis = await self.analyzer.analyze_content(
                    url=item['url'],
                    title=item['title'],
                    content=content_for_analysis,
                    keywords=item['keywords']
                )
                
                if analysis:
                    # Update the content hash to match the historical data
                    analysis.content_hash = item['content_hash']
                    results.append(analysis)
                    self.success_count += 1
                    logger.info(f"✅ Analysis completed: {analysis.threat_level} threat level")
                else:
                    self.failed_count += 1
                    logger.warning(f"⚠️  Analysis failed for: {item['url']}")
                
                # Rate limiting
                await asyncio.sleep(1.5)  # 1.5 seconds between requests
                
            except Exception as e:
                logger.error(f"❌ Error analyzing {item.get('url', 'unknown')}: {e}")
                self.failed_count += 1
                
            self.processed_count += 1
            
            # Progress update every 10 items
            if self.processed_count % 10 == 0:
                logger.info(f"📈 Progress: {self.processed_count} processed, {self.success_count} successful, {self.failed_count} failed")
        
        return results
    
    def save_ai_analyses(self, analyses: List[ThreatAnalysis]) -> int:
        """Save AI analyses to database"""
        saved_count = 0
        
        for analysis in analyses:
            try:
                # Convert ThreatAnalysis to dict for database storage
                analysis_data = {
                    'content_hash': analysis.content_hash,
                    'url': '',  # Will be populated from content_hash lookup if needed
                    'threat_level': analysis.threat_level,
                    'threat_categories': analysis.threat_categories,
                    'suspicious_indicators': analysis.suspicious_indicators,
                    'illegal_content_detected': analysis.illegal_content_detected,
                    'confidence_score': analysis.confidence_score,
                    'analysis_summary': analysis.analysis_summary,
                    'recommended_actions': analysis.recommended_actions,
                    'ai_reasoning': analysis.ai_reasoning,
                    'threat_signature': self.analyzer.create_threat_signature(analysis)
                }
                
                # Save to database
                result_id = self.db.insert_ai_analysis(analysis_data)
                if result_id > 0:
                    saved_count += 1
                    
                    # Update threat signature
                    self.db.update_threat_signature(
                        analysis_data['threat_signature'],
                        analysis.threat_level,
                        analysis.threat_categories + analysis.suspicious_indicators,
                        analysis.confidence_score
                    )
                    
            except Exception as e:
                logger.error(f"❌ Error saving analysis: {e}")
        
        logger.info(f"💾 Saved {saved_count} AI analyses to database")
        return saved_count
    
    async def analyze_all_historical_data(self, limit: int = None):
        """Analyze all historical data"""
        logger.info("🚀 Starting historical data AI analysis...")
        start_time = datetime.now()
        
        # Get historical data
        historical_data = self.get_historical_data(limit)
        
        if not historical_data:
            logger.info("ℹ️  No historical data found to analyze")
            return
        
        total_items = len(historical_data)
        logger.info(f"📊 Total items to analyze: {total_items}")
        
        # Process in batches
        all_analyses = []
        
        for i in range(0, total_items, self.batch_size):
            batch = historical_data[i:i + self.batch_size]
            logger.info(f"🔄 Processing batch {i//self.batch_size + 1} ({len(batch)} items)")
            
            try:
                batch_results = await self.analyze_batch(batch)
                all_analyses.extend(batch_results)
                
                # Save batch results immediately
                if batch_results:
                    self.save_ai_analyses(batch_results)
                
            except Exception as e:
                logger.error(f"❌ Error processing batch: {e}")
            
            # Longer pause between batches
            if i + self.batch_size < total_items:
                logger.info("⏸️  Pausing between batches...")
                await asyncio.sleep(5)
        
        # Final statistics
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("🎉 Historical data analysis completed!")
        logger.info(f"⏱️  Total time: {duration}")
        logger.info(f"📊 Total processed: {self.processed_count}")
        logger.info(f"✅ Successful analyses: {self.success_count}")
        logger.info(f"❌ Failed analyses: {self.failed_count}")
        logger.info(f"💾 Total analyses saved: {len(all_analyses)}")
        
        # Generate intelligence report
        if all_analyses:
            logger.info("📈 Generating intelligence report...")
            report = self.analyzer.generate_intelligence_report(all_analyses)
            
            # Save report to file
            with open('historical_intelligence_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info("📄 Intelligence report saved to: historical_intelligence_report.json")
            
            # Print summary
            print("\n" + "="*60)
            print("🧠 TRINETRA 3.0 - Historical AI Analysis Summary")
            print("="*60)
            print(f"📊 Total Items Analyzed: {report['total_items_analyzed']}")
            print(f"🚨 Critical Threats: {report['threat_summary']['critical_threats']}")
            print(f"⚠️  High Threats: {report['threat_summary']['high_threats']}")
            print(f"📝 Medium Threats: {report['threat_summary']['medium_threats']}")
            print(f"ℹ️  Low Threats: {report['threat_summary']['low_threats']}")
            print(f"✅ Benign Content: {report['threat_summary']['benign_content']}")
            print(f"🚫 Illegal Content Detected: {report['illegal_content_count']}")
            print("="*60)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze historical data with AI")
    parser.add_argument("--limit", type=int, help="Limit number of records to analyze")
    parser.add_argument("--batch-size", type=int, default=5, help="Batch size for processing")
    parser.add_argument("--test-connection", action="store_true", help="Test AI connection only")
    
    args = parser.parse_args()
    
    if args.test_connection:
        # Test AI connection
        logger.info("🧪 Testing AI connection...")
        try:
            test_analysis = gemini_analyzer.analyze_content_sync(
                url="http://test.onion",
                title="Test Page",
                content="This is a test page for testing AI connectivity.",
                keywords=["test"]
            )
            
            if test_analysis:
                logger.info("✅ AI connection test successful!")
                print("✅ AI Connection: SUCCESS")
                print(f"   Model: gemini-2.0-flash")
                print(f"   Test Analysis: {test_analysis.threat_level} threat level")
                return
            else:
                logger.error("❌ AI connection test failed!")
                print("❌ AI Connection: FAILED")
                return
                
        except Exception as e:
            logger.error(f"❌ AI connection error: {e}")
            print(f"❌ AI Connection: FAILED - {e}")
            return
    
    # Run historical analysis
    analyzer = HistoricalDataAnalyzer(batch_size=args.batch_size)
    
    try:
        asyncio.run(analyzer.analyze_all_historical_data(args.limit))
    except KeyboardInterrupt:
        logger.info("🛑 Analysis interrupted by user")
        print(f"\n📊 Progress when interrupted: {analyzer.processed_count} processed")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
