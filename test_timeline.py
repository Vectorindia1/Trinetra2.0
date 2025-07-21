#!/usr/bin/env python3
"""
Test script to debug Timeline Analysis issues
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.models import db_manager

def test_timeline_analysis():
    print("🔍 Testing Timeline Analysis functionality...")
    
    try:
        # Test database connection
        print("📊 Testing database connection...")
        ai_analyses = db_manager.get_ai_analyses(limit=1000)
        print(f"✅ Found {len(ai_analyses)} AI analyses")
        
        if not ai_analyses:
            print("❌ No AI analyses found!")
            return False
            
        # Test data processing
        print("🔄 Testing data processing...")
        timeline_data = []
        
        for analysis in ai_analyses:
            try:
                timestamp = pd.to_datetime(analysis.get('processed_at'))
                threat_level = analysis.get('threat_level', 'LOW')
                confidence = analysis.get('confidence_score', 0.0)
                illegal_detected = analysis.get('illegal_content_detected', 0)
                
                timeline_data.append({
                    'timestamp': timestamp,
                    'threat_level': threat_level,
                    'confidence': confidence,
                    'illegal_content': bool(illegal_detected),
                    'url': analysis.get('url', 'Unknown')
                })
            except Exception as e:
                print(f"⚠️ Error processing analysis: {e}")
                continue
        
        print(f"✅ Successfully processed {len(timeline_data)} items")
        
        if not timeline_data:
            print("❌ No timeline data could be processed!")
            return False
        
        # Create DataFrame
        print("📋 Creating DataFrame...")
        df = pd.DataFrame(timeline_data)
        print(f"✅ DataFrame created with shape: {df.shape}")
        print(f"📊 Threat level distribution: {df['threat_level'].value_counts().to_dict()}")
        
        # Test hourly aggregation
        print("⏰ Testing hourly aggregation...")
        df['hour'] = df['timestamp'].dt.floor('H')
        hourly_threat_counts = df.groupby(['hour', 'threat_level']).size().reset_index(name='count')
        print(f"✅ Hourly aggregation created with {len(hourly_threat_counts)} rows")
        
        # Test chart creation
        print("📈 Testing chart creation...")
        threat_colors = {
            'CRITICAL': '#dc2626',
            'HIGH': '#ef4444',
            'MEDIUM': '#f59e0b', 
            'LOW': '#22c55e',
            'BENIGN': '#6b7280'
        }
        
        # Create timeline chart
        fig_timeline = px.line(
            hourly_threat_counts,
            x='hour',
            y='count', 
            color='threat_level',
            color_discrete_map=threat_colors,
            title="🎯 AI-Detected Threats Over Time",
            markers=True
        )
        
        print("✅ Timeline chart created successfully")
        
        # Test confidence chart
        print("🎯 Testing confidence chart...")
        hourly_confidence = df.groupby('hour').agg({
            'confidence': ['mean', 'min', 'max', 'count']
        }).reset_index()
        hourly_confidence.columns = ['hour', 'avg_confidence', 'min_confidence', 'max_confidence', 'analysis_count']
        
        print(f"✅ Confidence aggregation created with {len(hourly_confidence)} rows")
        
        # Test metrics
        print("📊 Testing metrics calculation...")
        total_analyses = len(df)
        critical_high = len(df[df['threat_level'].isin(['CRITICAL', 'HIGH'])])
        illegal_content_count = len(df[df['illegal_content'] == True])
        avg_confidence = df['confidence'].mean()
        
        print(f"📋 Metrics:")
        print(f"   - Total analyses: {total_analyses}")
        print(f"   - High-risk threats: {critical_high}")
        print(f"   - Illegal content: {illegal_content_count}")
        print(f"   - Average confidence: {avg_confidence:.1%}")
        
        print("✅ All timeline analysis components working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Timeline analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_timeline_analysis()
