#!/bin/bash

echo "🚀 TRINETRA 3.0 - AI Enhancement Installation Script"
echo "=================================================="

# Check if virtual environment exists
if [ ! -d "tor-env" ]; then
    echo "❌ Virtual environment not found. Please run this from the darknet_crawler directory."
    exit 1
fi

# Activate virtual environment
source tor-env/bin/activate

echo "📦 Installing AI dependencies..."

# Install AI and ML packages
pip install --upgrade pip
pip install google-generativeai
pip install plotly>=5.0.0
pip install pandas>=1.5.0
pip install numpy>=1.21.0
pip install wordcloud>=1.9.0
pip install streamlit-autorefresh
pip install matplotlib>=3.5.0
pip install psutil>=5.9.0

echo "🧪 Testing Gemini AI connection..."

# Create test script
cat > test_ai.py << 'EOF'
#!/usr/bin/env python3
"""Test script for Gemini AI integration"""

try:
    print("🧠 Testing AI module import...")
    from ai.gemini_analyzer import gemini_analyzer, analyze_with_ai_sync
    print("✅ AI module imported successfully!")
    
    print("🔗 Testing API connection...")
    test_result = gemini_analyzer.analyze_content_sync(
        url="http://test.onion",
        title="Test Page", 
        content="This is a test page for darknet analysis.",
        keywords=["test"]
    )
    
    if test_result:
        print(f"✅ AI Analysis successful! Threat level: {test_result.threat_level}")
        print(f"📊 Confidence: {test_result.confidence_score:.1%}")
        print(f"📝 Summary: {test_result.analysis_summary}")
    else:
        print("⚠️  AI Analysis returned no results")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Test failed: {e}")
    print("Make sure your Gemini API key is correct in ai/gemini_analyzer.py")

print("\n🎯 AI Enhancement installation complete!")
print("🚀 You can now use the AI Analysis tab in the dashboard")
EOF

# Run the test
python test_ai.py

# Clean up test file
rm test_ai.py

echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start the dashboard: streamlit run dashboard.py"
echo "2. Navigate to the '🤖 AI Analysis' tab"  
echo "3. Test the AI connection using the 'Test AI Connection' button"
echo ""
echo "⚠️  Note: Make sure your Gemini API key is correct in ai/gemini_analyzer.py"
echo "🔑 API Key location: ai/gemini_analyzer.py (line 35)"

deactivate
