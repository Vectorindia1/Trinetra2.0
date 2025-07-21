#!/bin/bash
"""
TRINETRA 3.0 - Cron Job Setup Script
Sets up automatic AI analysis tasks
"""

echo "🤖 Setting up TRINETRA 3.0 AI Analysis Cron Jobs..."

# Get current directory
SCRIPT_DIR="/home/vector/darknet_crawler"

# Create temporary cron file
TEMP_CRON=$(mktemp)

# Get existing crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || true

echo "" >> "$TEMP_CRON"
echo "# TRINETRA 3.0 - AI Analysis Automation" >> "$TEMP_CRON"
echo "# Run auto AI analysis every 30 minutes" >> "$TEMP_CRON"
echo "*/30 * * * * cd $SCRIPT_DIR && /usr/bin/python3 auto_ai_analysis.py >> /var/log/trinetra_ai.log 2>&1" >> "$TEMP_CRON"

echo "" >> "$TEMP_CRON"
echo "# Run comprehensive historical analysis daily at 2 AM (if new data available)" >> "$TEMP_CRON"
echo "0 2 * * * cd $SCRIPT_DIR && /usr/bin/python3 analyze_historical_data.py --limit 100 --batch-size 5 >> /var/log/trinetra_historical.log 2>&1" >> "$TEMP_CRON"

echo "" >> "$TEMP_CRON"
echo "# Generate intelligence report weekly on Sundays at 3 AM" >> "$TEMP_CRON"
echo "0 3 * * 0 cd $SCRIPT_DIR && /usr/bin/python3 -c \"" >> "$TEMP_CRON"
echo "from database.models import db_manager;" >> "$TEMP_CRON"
echo "from ai.gemini_analyzer import gemini_analyzer;" >> "$TEMP_CRON"
echo "import json;" >> "$TEMP_CRON"
echo "analyses = db_manager.get_ai_analyses(1000);" >> "$TEMP_CRON"
echo "if analyses:" >> "$TEMP_CRON"
echo "    from ai.gemini_analyzer import ThreatAnalysis;" >> "$TEMP_CRON"
echo "    from datetime import datetime;" >> "$TEMP_CRON"
echo "    threat_analyses = [];" >> "$TEMP_CRON"
echo "    for a in analyses:" >> "$TEMP_CRON"
echo "        ta = ThreatAnalysis(" >> "$TEMP_CRON"
echo "            content_hash=a['content_hash']," >> "$TEMP_CRON"
echo "            threat_level=a['threat_level']," >> "$TEMP_CRON"
echo "            threat_categories=a['threat_categories']," >> "$TEMP_CRON"
echo "            suspicious_indicators=a['suspicious_indicators']," >> "$TEMP_CRON"
echo "            illegal_content_detected=a['illegal_content_detected']," >> "$TEMP_CRON"
echo "            confidence_score=a['confidence_score']," >> "$TEMP_CRON"
echo "            analysis_summary=a['analysis_summary']," >> "$TEMP_CRON"
echo "            recommended_actions=a['recommended_actions']," >> "$TEMP_CRON"
echo "            ai_reasoning=a['ai_reasoning']," >> "$TEMP_CRON"
echo "            timestamp=a['processed_at']" >> "$TEMP_CRON"
echo "        );" >> "$TEMP_CRON"
echo "        threat_analyses.append(ta);" >> "$TEMP_CRON"
echo "    report = gemini_analyzer.generate_intelligence_report(threat_analyses);" >> "$TEMP_CRON"
echo "    with open('weekly_intelligence_report.json', 'w') as f:" >> "$TEMP_CRON"
echo "        json.dump(report, f, indent=2);" >> "$TEMP_CRON"
echo "    print(f'Weekly report generated: {len(threat_analyses)} analyses');" >> "$TEMP_CRON"
echo "\" >> /var/log/trinetra_weekly_report.log 2>&1" >> "$TEMP_CRON"

# Install the new crontab
crontab "$TEMP_CRON"

# Clean up
rm "$TEMP_CRON"

# Create log directory if it doesn't exist
sudo mkdir -p /var/log
sudo touch /var/log/trinetra_ai.log
sudo touch /var/log/trinetra_historical.log
sudo touch /var/log/trinetra_weekly_report.log
sudo chown vector:vector /var/log/trinetra_*.log

echo "✅ Cron jobs installed successfully!"
echo ""
echo "📋 TRINETRA 3.0 AI Analysis Schedule:"
echo "   🔄 Auto AI Analysis: Every 30 minutes"
echo "   📊 Historical Analysis: Daily at 2:00 AM"
echo "   📈 Weekly Intelligence Report: Sundays at 3:00 AM"
echo ""
echo "📁 Log files:"
echo "   • /var/log/trinetra_ai.log - Auto analysis logs"
echo "   • /var/log/trinetra_historical.log - Historical analysis logs"
echo "   • /var/log/trinetra_weekly_report.log - Weekly report logs"
echo ""
echo "🔍 To view current cron jobs: crontab -l"
echo "🗑️  To remove TRINETRA cron jobs: crontab -e (then delete lines)"
