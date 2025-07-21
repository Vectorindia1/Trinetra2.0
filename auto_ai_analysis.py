#!/usr/bin/env python3
"""
TRINETRA 3.0 - Auto AI Analysis Script  
Automatically analyzes new data that hasn't been processed by AI yet
Can be run via cron job or manually for continuous AI threat analysis
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime

# Add current directory to path for imports  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.gemini_analyzer import gemini_analyzer
from database.models import db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_ai_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def analyze_new_data():
    """Analyze any new data that hasn't been processed by AI yet"""
    logger.info("🔍 Checking for new data to analyze...")
    
    try:
        # Get new data from alerts table that hasn't been AI analyzed
        with db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT a.url, a.title, a.keywords_found, a.content_hash
                FROM alerts a
                LEFT JOIN ai_analysis ai ON a.content_hash = ai.content_hash  
                WHERE ai.content_hash IS NULL
                LIMIT 20
            """)
            
            new_data = cursor.fetchall()
            
        if not new_data:
            logger.info("✅ No new data to analyze")
            return
            
        logger.info(f"📊 Found {len(new_data)} new items to analyze")
        
        # Process each item
        for row in new_data:
            try:
                # Parse keywords
                try:
                    keywords = json.loads(row['keywords_found']) if row['keywords_found'] else []
                except json.JSONDecodeError:
                    keywords = []
                
                # Create content for analysis
                content = f"Title: {row['title'] or ''}\nKeywords Found: {', '.join(keywords)}"
                
                # Analyze with AI
                analysis = await gemini_analyzer.analyze_content(
                    url=row['url'],
                    title=row['title'] or '',
                    content=content,
                    keywords=keywords
                )
                
                if analysis:
                    # Update content hash to match historical data
                    analysis.content_hash = row['content_hash']
                    
                    # Save AI analysis to database
                    analysis_data = {
                        'content_hash': analysis.content_hash,
                        'url': row['url'],
                        'threat_level': analysis.threat_level,
                        'threat_categories': analysis.threat_categories,
                        'suspicious_indicators': analysis.suspicious_indicators,
                        'illegal_content_detected': analysis.illegal_content_detected,
                        'confidence_score': analysis.confidence_score,
                        'analysis_summary': analysis.analysis_summary,
                        'recommended_actions': analysis.recommended_actions,
                        'ai_reasoning': analysis.ai_reasoning,
                        'threat_signature': gemini_analyzer.create_threat_signature(analysis)
                    }
                    
                    result_id = db_manager.insert_ai_analysis(analysis_data)
                    
                    if result_id > 0:
                        # Update threat signature
                        db_manager.update_threat_signature(
                            analysis_data['threat_signature'],
                            analysis.threat_level,
                            analysis.threat_categories + analysis.suspicious_indicators,
                            analysis.confidence_score
                        )
                        
                        logger.info(f"✅ AI Analysis saved: {row['url']} - {analysis.threat_level} threat")
                    else:
                        logger.warning(f"⚠️  Failed to save analysis for: {row['url']}")
                else:
                    logger.warning(f"⚠️  AI analysis failed for: {row['url']}")
                    
                # Rate limiting
                await asyncio.sleep(1.5)
                
            except Exception as e:
                logger.error(f"❌ Error processing {row['url']}: {e}")
        
        logger.info("🎉 Auto AI analysis completed")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in auto analysis: {e}")

def main():
    """Main function"""
    logger.info("🤖 TRINETRA 3.0 - Auto AI Analysis Starting...")
    
    try:
        asyncio.run(analyze_new_data())
    except KeyboardInterrupt:
        logger.info("🛑 Auto analysis interrupted")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
