import streamlit as st
import json
import pandas as pd
import os
from collections import Counter
from datetime import datetime
from wordcloud import WordCloud
from streamlit_autorefresh import st_autorefresh
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import subprocess
# ============================
# Enhanced Page Configuration
# ============================
st.set_page_config(
    page_title="🕵 TRINETRA ",
    page_icon="🕵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# Loaders with Enhanced Error Handling
# ============================
def load_database_alerts(limit=100):
    """Load alerts from database for real-time updates"""
    try:
        from database.models import db_manager
        alerts = db_manager.get_alerts(limit=limit)
        
        # Convert database rows to dictionary format compatible with existing code
        processed_alerts = []
        for alert in alerts:
            processed_alert = dict(alert)
            # Parse keywords_found if it's a JSON string
            if 'keywords_found' in processed_alert and isinstance(processed_alert['keywords_found'], str):
                try:
                    processed_alert['keywords_found'] = json.loads(processed_alert['keywords_found'])
                except:
                    processed_alert['keywords_found'] = []
            processed_alerts.append(processed_alert)
        
        return processed_alerts
    except Exception as e:
        st.warning(f"⚠️ Could not load database alerts: {e}")
        return []
def load_alerts(path="alert_log.json"):
    try:
        with open(path, "r", encoding='utf-8') as f:
            alerts = [json.loads(line) for line in f if line.strip()]
        return alerts
    except FileNotFoundError:
        st.warning(f"⚠️ Alert log file not found at {path}")
        return []
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON decode error: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error loading alerts: {e}")
        return []

def load_visited(path="visited_links.json"):
    try:
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning(f"⚠️ Visited links file not found at {path}")
        return []
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON decode error: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error loading visited links: {e}")
        return []

def load_non_http(path="non_http_links.json"):
    try:
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning(f"⚠️ Non-HTTP links file not found at {path}")
        return []
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON decode error: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error loading non-HTTP links: {e}")
        return []

def load_logs(path="crawler.log"):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding='utf-8') as f:
                return f.read().splitlines()[-100:]  # Increased to 100 lines
        else:
            st.warning(f"⚠️ Log file not found at {path}")
            return ["Log file not found."]
    except Exception as e:
        st.error(f"❌ Error loading logs: {e}")
        return [f"Error loading logs: {e}"]

# ============================
# Enhanced Styling with Spooky Theme
# ============================
def set_enhanced_theme():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
            
            /* Global Styles */
            .stApp {
                background: linear-gradient(135deg, #0a0a0a 0%, #1a0d2e 25%, #16213e 50%, #0f3460 75%, #0a0a0a 100%);
                background-size: 400% 400%;
                animation: gradientShift 15s ease infinite;
                min-height: 100vh;
                position: relative;
                overflow-x: hidden;
            }
            
            @keyframes gradientShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            /* Floating Cubes Animation */
            .stApp::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: -1;
                background-image: 
                    radial-gradient(2px 2px at 20px 30px, rgba(255,255,255,0.1), transparent),
                    radial-gradient(2px 2px at 40px 70px, rgba(147,51,234,0.2), transparent),
                    radial-gradient(1px 1px at 90px 40px, rgba(79,70,229,0.3), transparent),
                    radial-gradient(1px 1px at 130px 80px, rgba(236,72,153,0.2), transparent),
                    radial-gradient(2px 2px at 160px 30px, rgba(34,197,94,0.1), transparent);
                background-repeat: repeat;
                background-size: 200px 200px;
                animation: floatingCubes 20s linear infinite;
            }
            
            @keyframes floatingCubes {
                0% { transform: translate(0, 0) rotate(0deg); }
                33% { transform: translate(30px, -30px) rotate(120deg); }
                66% { transform: translate(-20px, 20px) rotate(240deg); }
                100% { transform: translate(0, 0) rotate(360deg); }
            }
            
            /* Glass Morphism Enhanced */
            .glass-container {
                backdrop-filter: blur(20px) saturate(180%);
                background: rgba(17, 25, 40, 0.3);
                border-radius: 20px;
                padding: 2rem;
                margin: 1.5rem 0;
                border: 1px solid rgba(147, 51, 234, 0.3);
                box-shadow: 
                    0 8px 32px rgba(147, 51, 234, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
            }
            
            .glass-container::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(147,51,234,0.1) 0%, transparent 70%);
                animation: shimmer 8s ease-in-out infinite;
                pointer-events: none;
            }
            
            @keyframes shimmer {
                0%, 100% { transform: rotate(0deg); opacity: 0.5; }
                50% { transform: rotate(180deg); opacity: 0.8; }
            }
            
            /* Main Title */
            .main-title {
                font-family: 'Orbitron', monospace;
                font-size: 3.5rem;
                font-weight: 900;
                text-align: center;
                background: linear-gradient(45deg, #9333ea, #7c3aed, #ec4899, #06b6d4);
                background-size: 400% 400%;
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                animation: gradientText 3s ease infinite;
                text-shadow: 0 0 30px rgba(147, 51, 234, 0.5);
                margin: 2rem 0;
                position: relative;
            }
            
            @keyframes gradientText {
                0%, 100% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
            }
            
            /* Sidebar Styling */
            .css-1d391kg {
                background: rgba(17, 25, 40, 0.6);
                backdrop-filter: blur(15px);
                border-right: 1px solid rgba(147, 51, 234, 0.3);
            }
            
            /* Metric Cards */
            .metric-card {
                background: rgba(147, 51, 234, 0.1);
                border: 1px solid rgba(147, 51, 234, 0.3);
                border-radius: 15px;
                padding: 1.5rem;
                margin: 1rem 0;
                text-align: center;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(147, 51, 234, 0.4);
                border-color: rgba(147, 51, 234, 0.6);
            }
            
            .metric-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                transition: left 0.5s;
            }
            
            .metric-card:hover::before {
                left: 100%;
            }
            
            .metric-value {
                font-family: 'Orbitron', monospace;
                font-size: 2.5rem;
                font-weight: 700;
                color: #9333ea;
                display: block;
                margin-bottom: 0.5rem;
            }
            
            .metric-label {
                font-family: 'Rajdhani', sans-serif;
                font-size: 1.1rem;
                color: #e2e8f0;
                font-weight: 500;
            }
            
            /* Alert Cards */
            .alert-card {
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 15px;
                padding: 1.5rem;
                margin: 1rem 0;
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
                position: relative;
            }
            
            .alert-card:hover {
                transform: translateX(5px);
                box-shadow: 0 5px 20px rgba(239, 68, 68, 0.3);
            }
            
            .alert-card.medium {
                background: rgba(251, 191, 36, 0.1);
                border-color: rgba(251, 191, 36, 0.3);
            }
            
            .alert-card.medium:hover {
                box-shadow: 0 5px 20px rgba(251, 191, 36, 0.3);
            }
            
            .alert-card.low {
                background: rgba(34, 197, 94, 0.1);
                border-color: rgba(34, 197, 94, 0.3);
            }
            
            .alert-card.low:hover {
                box-shadow: 0 5px 20px rgba(34, 197, 94, 0.3);
            }
            
            /* Typography */
            h1, h2, h3 {
                font-family: 'Orbitron', monospace;
                color: #e2e8f0;
            }
            
            p, div, span {
                font-family: 'Rajdhani', sans-serif;
                color: #cbd5e1;
            }
            
            /* Buttons */
            .stButton > button {
                background: linear-gradient(45deg, #9333ea, #7c3aed);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0.75rem 2rem;
                font-family: 'Rajdhani', sans-serif;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(147, 51, 234, 0.3);
            }
            
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(147, 51, 234, 0.4);
            }
            
            /* Input Fields */
            .stTextInput > div > div > input {
                background: rgba(17, 25, 40, 0.8);
                border: 1px solid rgba(147, 51, 234, 0.3);
                border-radius: 10px;
                color: #e2e8f0;
                font-family: 'Rajdhani', sans-serif;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: rgba(147, 51, 234, 0.6);
                box-shadow: 0 0 0 1px rgba(147, 51, 234, 0.3);
            }
            
            /* Selectbox */
            .stSelectbox > div > div > select {
                background: rgba(17, 25, 40, 0.8);
                border: 1px solid rgba(147, 51, 234, 0.3);
                border-radius: 10px;
                color: #e2e8f0;
                font-family: 'Rajdhani', sans-serif;
            }
            
            /* Code blocks */
            .stCode {
                background: rgba(0, 0, 0, 0.6);
                border: 1px solid rgba(147, 51, 234, 0.3);
                border-radius: 10px;
            }
            
            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: rgba(17, 25, 40, 0.3);
            }
            
            ::-webkit-scrollbar-thumb {
                background: linear-gradient(45deg, #9333ea, #7c3aed);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: linear-gradient(45deg, #7c3aed, #6366f1);
            }
        </style>
    """, unsafe_allow_html=True)

# ============================
# Enhanced Categorization
# ============================
def get_severity(keyword):
    high_severity = ["bomb", "terror", "attack", "kill", "explosive", "weapon", "assassination", "murder", "violence"]
    medium_severity = ["carding", "hacking", "drugs", "malware", "exploit", "phishing", "fraud", "stealing", "ransomware"]
    low_severity = ["privacy", "anonymous", "vpn", "tor", "encrypted", "secure", "hidden", "private"]
    
    keyword_lower = keyword.lower()
    
    if any(k in keyword_lower for k in high_severity):
        return "High"
    elif any(k in keyword_lower for k in medium_severity):
        return "Medium"
    else:
        return "Low"

def get_severity_color(severity):
    colors = {
        "High": "#ef4444",
        "Medium": "#f59e0b", 
        "Low": "#22c55e"
    }
    return colors.get(severity, "#6b7280")

# ============================
# Enhanced Components
# ============================
def create_metric_card(title, value, icon="📊"):
    st.markdown(f"""
        <div class="metric-card">
            <span class="metric-value">{value}</span>
            <div class="metric-label">{icon} {title}</div>
        </div>
    """, unsafe_allow_html=True)

def create_alert_card(alert):
    severity = "low"
    for keyword in alert.get("keywords_found", []):
        sev = get_severity(keyword)
        if sev == "High":
            severity = "high"
            break
        elif sev == "Medium":
            severity = "medium"
    
    timestamp = alert.get('timestamp', 'Unknown')
    url = alert.get('url', 'No URL')
    title = alert.get('title', 'No Title')
    keywords = ', '.join(alert.get('keywords_found', []))
    
    st.markdown(f"""
        <div class="alert-card {severity}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <span style="font-weight: 600; color: #e2e8f0;">🚨 Alert - {severity.upper()} Priority</span>
                <span style="font-size: 0.9rem; color: #94a3b8;">📅 {timestamp}</span>
            </div>
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: #e2e8f0;">🔗 URL:</strong> 
                <a href="{url}" target="_blank" style="color: #9333ea; text-decoration: none;">{url}</a>
            </div>
            <div style="margin-bottom: 0.5rem;">
                <strong style="color: #e2e8f0;">📖 Title:</strong> 
                <span style="color: #cbd5e1;">{title}</span>
            </div>
            <div>
                <strong style="color: #e2e8f0;">🔍 Keywords:</strong> 
                <code style="background: rgba(0,0,0,0.3); padding: 0.2rem 0.5rem; border-radius: 5px; color: #9333ea;">{keywords}</code>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ============================
# Main Application
# ============================
def main():
    # Set theme
    set_enhanced_theme()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Control Panel")
        st.markdown("---")
        
        # Navigation
        menu = st.radio(
            "🧭 Navigation",
            [
                "📊 Dashboard Overview",
                "📈 AI Keyword Analytics", 
                "⏰ AI Timeline Analysis",
                "🔍 Alert Browser",
                "🤖 AI Analysis",
                "🧠 Live Monitoring"
            ],
            key="navigation"
        )
        
        st.markdown("---")
        
 

        st.markdown("### 🧪 Manual TOR Scraper")
        tor_link_input = st.text_input("🔗 Enter TOR Link (.onion)", placeholder="http://example.onion")

        if st.button("🕷 Start Scraping"):
            if tor_link_input.strip():
                with st.spinner("⏳ Starting TOR Scraper in background..."):
                    try:
                        # Create the command to run scrapy with the virtual environment
                        venv_python = "/home/vector/darknet_crawler/tor-env/bin/python"
                        scrapy_cmd = "/home/vector/darknet_crawler/tor-env/bin/scrapy"
                        
                        # Validate URL
                        url = tor_link_input.strip()
                        if not url.startswith(('http://', 'https://')):
                            url = 'http://' + url
                        
                        # Launch scraper with proper environment
                        process = subprocess.Popen(
                            [
                                scrapy_cmd, "crawl", "onion",
                                "-a", f"start_url={url}",
                                "-s", "LOG_LEVEL=INFO",
                                "-s", "LOG_FILE=crawler.log"
                            ],
                            cwd="/home/vector/darknet_crawler",
                            stdout=open("/home/vector/darknet_crawler/crawler.log", "a"),
                            stderr=subprocess.STDOUT,
                            env={**os.environ, 'PATH': '/home/vector/darknet_crawler/tor-env/bin:' + os.environ.get('PATH', '')}
                        )
                        
                        st.success(f"🟢 Scraper started for: {url}")
                        st.info("📊 Check the Live Monitoring tab to see real-time progress")
                        
                        # Store the process info for monitoring
                        if 'scraper_processes' not in st.session_state:
                            st.session_state.scraper_processes = []
                        st.session_state.scraper_processes.append({
                            'pid': process.pid,
                            'url': url,
                            'start_time': datetime.now().isoformat()
                        })
                        
                    except Exception as ex:
                        st.error(f"❌ Failed to launch scraper: {ex}")
                        st.error("Check that the Tor service is running and the URL is valid")
            else:
                st.warning("⚠ Please enter a valid TOR link before scraping.")













    


        # Refresh button
        if st.button("🔄 Refresh Data", key="refresh"):
            st.cache_data.clear()
            st.rerun()
    
    # Main title
    st.markdown('<div class="main-title">🕵️ TRINETRA</div>', unsafe_allow_html=True)
    
    # Load data with error handling
    try:
        # Try to load from database first (real-time data)
        db_alerts = load_database_alerts(limit=200)
        if db_alerts:
            st.info(f"✅ Loaded {len(db_alerts)} alerts from database (real-time)")
            alerts = db_alerts
        else:
            # Fallback to JSON files
            alerts = load_alerts()
            if alerts:
                st.warning("⚠️ Using JSON file data (may not be up-to-date)")
        
        visited = load_visited()
        non_http = load_non_http()
        
        # Validate and clean data
        valid_alerts = []
        for alert in alerts:
            if isinstance(alert, dict) and "url" in alert and "keywords_found" in alert:
                valid_alerts.append(alert)
        
        all_keywords = []
        for alert in valid_alerts:
            keywords = alert.get("keywords_found", [])
            if isinstance(keywords, list):
                all_keywords.extend(keywords)
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return
    
    # ========== Dashboard Overview ==========
    if menu == "📊 Dashboard Overview":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card("Total Alerts", len(valid_alerts), "🚨")
        
        with col2:
            unique_urls = len(set(alert["url"] for alert in valid_alerts))
            create_metric_card("Unique URLs", unique_urls, "🌐")
        
        with col3:
            unique_keywords = len(set(all_keywords))
            create_metric_card("Unique Keywords", unique_keywords, "🔍")
        
        with col4:
            create_metric_card("Total Crawled", len(visited), "🕷️")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Recent alerts
        if valid_alerts:
            st.markdown('<div class="glass-container">', unsafe_allow_html=True)
            st.markdown("### 🔥 Recent High-Priority Alerts")
            
            # Sort by severity and show top 5
            sorted_alerts = sorted(valid_alerts, 
                                 key=lambda x: (max([get_severity(k) for k in x.get("keywords_found", [])], default="Low")), 
                                 reverse=True)[:5]
            
            for alert in sorted_alerts:
                create_alert_card(alert)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== AI Keyword Analytics ==========
    elif menu == "📈 AI Keyword Analytics":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 🤖 AI-Powered Keyword Intelligence Analysis")
        
        try:
            from database.models import db_manager
            ai_analyses = db_manager.get_ai_analyses(limit=500)
            ai_stats = db_manager.get_ai_statistics()
            
            if ai_analyses:
                # Collect AI-identified threat categories and indicators
                ai_keywords = []
                keyword_to_urls = {}  # For hover details
                keyword_to_threat_levels = {}
                
                for analysis in ai_analyses:
                    url = analysis.get('url', 'Unknown')
                    threat_level = analysis.get('threat_level', 'LOW')
                    
                    # Collect threat categories
                    for category in analysis.get('threat_categories', []):
                        ai_keywords.append(category)
                        if category not in keyword_to_urls:
                            keyword_to_urls[category] = []
                            keyword_to_threat_levels[category] = []
                        keyword_to_urls[category].append(url)
                        keyword_to_threat_levels[category].append(threat_level)
                    
                    # Collect suspicious indicators
                    for indicator in analysis.get('suspicious_indicators', []):
                        ai_keywords.append(indicator)
                        if indicator not in keyword_to_urls:
                            keyword_to_urls[indicator] = []
                            keyword_to_threat_levels[indicator] = []
                        keyword_to_urls[indicator].append(url)
                        keyword_to_threat_levels[indicator].append(threat_level)
                
                if ai_keywords:
                    # AI Keyword Frequency Analysis
                    keyword_counts = Counter(ai_keywords)
                    top_keywords = keyword_counts.most_common(15)
                    
                    # Create enhanced interactive bar chart
                    keyword_df = pd.DataFrame(top_keywords, columns=["Keyword", "Frequency"])
                    
                    # Add threat level information
                    keyword_df['Avg_Threat_Level'] = keyword_df['Keyword'].apply(
                        lambda k: Counter(keyword_to_threat_levels.get(k, [])).most_common(1)[0][0] if keyword_to_threat_levels.get(k) else 'LOW'
                    )
                    
                    # Color mapping based on threat level
                    color_map = {
                        'CRITICAL': '#dc2626',
                        'HIGH': '#ef4444', 
                        'MEDIUM': '#f59e0b',
                        'LOW': '#22c55e',
                        'BENIGN': '#6b7280'
                    }
                    
                    keyword_df['Color'] = keyword_df['Avg_Threat_Level'].map(color_map)
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=keyword_df['Frequency'],
                            y=keyword_df['Keyword'],
                            orientation='h',
                            marker=dict(
                                color=keyword_df['Color'],
                                line=dict(color='rgba(255,255,255,0.2)', width=1)
                            ),
                            hovertemplate='<b>%{y}</b><br>' +
                                         'Frequency: %{x}<br>' +
                                         'Threat Level: %{customdata}<br>' +
                                         '<extra></extra>',
                            customdata=keyword_df['Avg_Threat_Level'],
                            texttemplate='%{x}',
                            textposition='inside',
                            textfont=dict(color='white', size=12)
                        )
                    ])
                    
                    fig.update_layout(
                        title=dict(
                            text="🎯 AI-Identified Threat Keywords & Categories",
                            font=dict(color='white', size=18, family='Orbitron')
                        ),
                        font=dict(family="Rajdhani, sans-serif", size=12, color="white"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            title="Frequency",
                            showgrid=True, 
                            gridcolor='rgba(255,255,255,0.1)',
                            color='white'
                        ),
                        yaxis=dict(
                            title="Keywords",
                            showgrid=False,
                            color='white'
                        ),
                        height=600,
                        margin=dict(l=150, r=50, t=80, b=50)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Interactive Keyword Details
                    st.markdown("#### 🔍 Interactive Keyword Explorer")
                    
                    # Create a selectbox for keyword selection
                    selected_keyword = st.selectbox(
                        "🎯 Select a keyword to view details:",
                        options=list(keyword_counts.keys()),
                        index=0 if keyword_counts else None
                    )
                    
                    if selected_keyword and selected_keyword in keyword_to_urls:
                        urls_for_keyword = keyword_to_urls[selected_keyword]
                        threat_levels_for_keyword = keyword_to_threat_levels[selected_keyword]
                        
                        # Create metrics for selected keyword
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            create_metric_card("Total Occurrences", len(urls_for_keyword), "📊")
                        with col2:
                            unique_urls = len(set(urls_for_keyword))
                            create_metric_card("Unique URLs", unique_urls, "🌐")
                        with col3:
                            most_common_threat = Counter(threat_levels_for_keyword).most_common(1)[0][0]
                            create_metric_card("Primary Threat Level", most_common_threat, "⚠️")
                        with col4:
                            critical_high = sum(1 for t in threat_levels_for_keyword if t in ['CRITICAL', 'HIGH'])
                            create_metric_card("High-Risk Instances", critical_high, "🔴")
                        
                        # Show URLs where this keyword appears
                        st.markdown(f"##### 🔗 URLs containing '{selected_keyword}':")
                        
                        # Create a dataframe for better display
                        url_data = []
                        for url, threat in zip(urls_for_keyword[:20], threat_levels_for_keyword[:20]):
                            url_data.append({
                                "URL": url,
                                "Threat Level": threat,
                                "Domain": url.split('/')[2] if '/' in url else url
                            })
                        
                        if url_data:
                            url_df = pd.DataFrame(url_data)
                            st.dataframe(
                                url_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    "URL": st.column_config.LinkColumn(
                                        "URL",
                                        help="Click to visit the URL",
                                        width="large"
                                    ),
                                    "Threat Level": st.column_config.TextColumn(
                                        "Threat Level",
                                        help="AI-assessed threat level",
                                        width="small"
                                    )
                                }
                            )
                            
                            if len(urls_for_keyword) > 20:
                                st.info(f"ℹ️ Showing first 20 of {len(urls_for_keyword)} URLs")
                    
                    # AI Statistics Overview
                    st.markdown("#### 📈 AI Keyword Analytics Summary")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        threat_categories_count = len([k for k in ai_keywords if any(analysis.get('threat_categories', []) for analysis in ai_analyses if k in analysis.get('threat_categories', []))])
                        create_metric_card("Threat Categories", len(set([k for analysis in ai_analyses for k in analysis.get('threat_categories', [])])), "🎯")
                    
                    with col2:
                        suspicious_indicators_count = len(set([k for analysis in ai_analyses for k in analysis.get('suspicious_indicators', [])]))
                        create_metric_card("Suspicious Indicators", suspicious_indicators_count, "🔍")
                    
                    with col3:
                        create_metric_card("Total AI Keywords", len(set(ai_keywords)), "🤖")
                
            else:
                st.info("💭 No AI analysis data available. Run the crawler with AI analysis enabled to see keyword intelligence.")
                
                # Fallback to regular keyword analysis
                if all_keywords:
                    st.markdown("#### 🔄 Fallback: Traditional Keyword Analysis")
                    keyword_counts = Counter(all_keywords)
                    pie_df = pd.DataFrame(keyword_counts.most_common(10), columns=["Keyword", "Count"])
                    
                    fig = px.pie(
                        pie_df, 
                        names="Keyword", 
                        values="Count",
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Viridis
                    )
                    
                    fig.update_layout(
                        font=dict(family="Rajdhani, sans-serif", color="white"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        except ImportError:
            st.error("❌ AI Analysis module not available. Please install required dependencies.")
        except Exception as e:
            st.error(f"❌ Error loading AI keyword analytics: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== AI Timeline Analysis ==========
    elif menu == "⏰ AI Timeline Analysis":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### ⏰ AI Threat Timeline Analysis")
        
        try:
            from database.models import db_manager
            ai_analyses = db_manager.get_ai_analyses(limit=1000)
            
            if ai_analyses:
                # Process AI analysis data for timeline visualization
                timeline_data = []
                
                for analysis in ai_analyses:
                    try:
                        # Convert processed_at timestamp
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
                        continue
                
                if timeline_data:
                    df = pd.DataFrame(timeline_data)
                    
                    # Create AI Timeline Analysis Overview
                    st.markdown("#### 📊 AI Threat Detection Overview")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_analyses = len(df)
                        create_metric_card("Total AI Analyses", total_analyses, "🧠")
                    
                    with col2:
                        critical_high = len(df[df['threat_level'].isin(['CRITICAL', 'HIGH'])])
                        create_metric_card("High-Risk Threats", critical_high, "🚨")
                    
                    with col3:
                        illegal_content_count = len(df[df['illegal_content'] == True])
                        create_metric_card("Illegal Content", illegal_content_count, "⚠️")
                    
                    with col4:
                        avg_confidence = df['confidence'].mean()
                        create_metric_card("Avg AI Confidence", f"{avg_confidence:.1%}", "📊")
                    
                    # Threat Level Timeline
                    st.markdown("#### 📈 Threat Level Distribution Over Time")
                    
                    # Hourly aggregation by threat level
                    df['hour'] = df['timestamp'].dt.floor('h')
                    hourly_threat_counts = df.groupby(['hour', 'threat_level']).size().reset_index(name='count')
                    
                    # Debug info
                    st.write(f"Debug: DataFrame shape: {df.shape}")
                    st.write(f"Debug: Hourly counts shape: {hourly_threat_counts.shape}")
                    st.write(f"Debug: Threat levels: {df['threat_level'].value_counts().to_dict()}")
                    
                    # Enhanced color mapping for threat levels
                    threat_colors = {
                        'CRITICAL': '#dc2626',
                        'HIGH': '#ef4444',
                        'MEDIUM': '#f59e0b', 
                        'LOW': '#22c55e',
                        'BENIGN': '#6b7280'
                    }
                    
                    # Create interactive timeline chart
                    fig_timeline = px.line(
                        hourly_threat_counts,
                        x='hour',
                        y='count', 
                        color='threat_level',
                        color_discrete_map=threat_colors,
                        title="🎯 AI-Detected Threats Over Time",
                        markers=True
                    )
                    
                    fig_timeline.update_layout(
                        title=dict(
                            font=dict(color='white', size=18, family='Orbitron')
                        ),
                        font=dict(family="Rajdhani, sans-serif", color="white"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            title="Time", 
                            showgrid=True, 
                            gridcolor='rgba(255,255,255,0.1)',
                            color='white'
                        ),
                        yaxis=dict(
                            title="Threat Count", 
                            showgrid=True, 
                            gridcolor='rgba(255,255,255,0.1)',
                            color='white'
                        ),
                        legend=dict(
                            bgcolor='rgba(0,0,0,0.5)',
                            bordercolor='rgba(255,255,255,0.2)'
                        ),
                        height=500
                    )
                    
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    # AI Confidence Score Timeline
                    st.markdown("#### 🎯 AI Confidence Distribution")
                    
                    # Hourly confidence aggregation
                    hourly_confidence = df.groupby('hour').agg({
                        'confidence': ['mean', 'min', 'max', 'count']
                    }).reset_index()
                    hourly_confidence.columns = ['hour', 'avg_confidence', 'min_confidence', 'max_confidence', 'analysis_count']
                    
                    # Create confidence timeline with error bands
                    fig_confidence = go.Figure()
                    
                    # Add confidence band
                    fig_confidence.add_trace(go.Scatter(
                        x=list(hourly_confidence['hour']) + list(hourly_confidence['hour'][::-1]),
                        y=list(hourly_confidence['max_confidence']) + list(hourly_confidence['min_confidence'][::-1]),
                        fill='tonexty',
                        fillcolor='rgba(99, 102, 241, 0.2)',
                        line=dict(color='rgba(255,255,255,0)'),
                        hoverinfo="skip",
                        showlegend=False,
                        name='Confidence Range'
                    ))
                    
                    # Add average confidence line
                    fig_confidence.add_trace(go.Scatter(
                        x=hourly_confidence['hour'],
                        y=hourly_confidence['avg_confidence'],
                        mode='lines+markers',
                        name='Average Confidence',
                        line=dict(color='#6366f1', width=3),
                        marker=dict(size=8, color='#6366f1')
                    ))
                    
                    fig_confidence.update_layout(
                        title=dict(
                            text="🎯 AI Analysis Confidence Over Time",
                            font=dict(color='white', size=18, family='Orbitron')
                        ),
                        font=dict(family="Rajdhani, sans-serif", color="white"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            title="Time",
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.1)', 
                            color='white'
                        ),
                        yaxis=dict(
                            title="Confidence Score",
                            showgrid=True,
                            gridcolor='rgba(255,255,255,0.1)',
                            color='white',
                            tickformat='.0%'
                        ),
                        legend=dict(
                            bgcolor='rgba(0,0,0,0.5)',
                            bordercolor='rgba(255,255,255,0.2)'
                        ),
                        height=400
                    )
                    
                    st.plotly_chart(fig_confidence, use_container_width=True)
                    
                    # Recent High-Risk Detections
                    st.markdown("#### 🚨 Recent High-Risk Detections")
                    
                    high_risk_df = df[df['threat_level'].isin(['CRITICAL', 'HIGH'])].sort_values('timestamp', ascending=False).head(10)
                    
                    if not high_risk_df.empty:
                        for _, detection in high_risk_df.iterrows():
                            with st.expander(f"🚨 {detection['threat_level']} - {detection['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**🌐 URL:** {detection['url'][:100]}..." if len(detection['url']) > 100 else f"**🌐 URL:** {detection['url']}")
                                    st.write(f"**⚠️ Threat Level:** {detection['threat_level']}")
                                
                                with col2:
                                    st.write(f"**🎯 Confidence:** {detection['confidence']:.1%}")
                                    st.write(f"**🚫 Illegal Content:** {'Yes' if detection['illegal_content'] else 'No'}")
                    else:
                        st.info("✅ No high-risk threats detected recently")
                    
                else:
                    st.warning("📊 AI analysis data exists but could not be processed for timeline visualization")
            else:
                st.info("💭 No AI analysis data available. Run the crawler with AI analysis enabled to see threat timeline.")
                
                # Show fallback message with instructions
                st.markdown("""
                ### 🚀 Getting Started with AI Timeline Analysis
                
                To see threat timeline data:
                1. Enable AI analysis in your crawler configuration
                2. Run the darknet crawler to collect and analyze URLs
                3. Return to this dashboard to view AI-powered threat trends
                
                **Features you'll see:**
                - Real-time threat level distribution over time
                - AI confidence score tracking
                - High-risk detection alerts
                - Interactive timeline visualizations
                """)
                
        except ImportError:
            st.error("❌ AI Analysis module not available. Please install required dependencies.")
        except Exception as e:
            st.error(f"❌ Error loading AI timeline analysis: {e}")
            st.write(f"Debug info: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Alert Browser ==========
    elif menu == "🔍 Alert Browser":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 🔍 Advanced Alert Search & Filter")
        
        # Search filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            keyword_filter = st.text_input("🔎 Filter by Keyword:", placeholder="Enter keyword...")
        
        with col2:
            domain_filter = st.text_input("🌐 Filter by Domain:", placeholder="Enter domain...")
        
        with col3:
            severity_filter = st.selectbox("🚨 Filter by Severity:", ["All", "High", "Medium", "Low"])
        
        # Apply filters
        filtered_alerts = valid_alerts.copy()
        
        if keyword_filter:
            filtered_alerts = [
                alert for alert in filtered_alerts 
                if any(keyword_filter.lower() in k.lower() for k in alert.get("keywords_found", []))
            ]
        
        if domain_filter:
            filtered_alerts = [
                alert for alert in filtered_alerts 
                if domain_filter.lower() in alert.get("url", "").lower()
            ]
        
        if severity_filter != "All":
            filtered_alerts = [
                alert for alert in filtered_alerts 
                if any(get_severity(k) == severity_filter for k in alert.get("keywords_found", []))
            ]
        
        st.markdown(f"**Found {len(filtered_alerts)} alerts matching your criteria**")
        
        # Display filtered alerts
        for alert in filtered_alerts[:20]:  # Limit to 20 for performance
            create_alert_card(alert)
        
        if len(filtered_alerts) > 20:
            st.info(f"Showing first 20 of {len(filtered_alerts)} alerts. Refine your search for more specific results.")
        
        # Export functionality
        if filtered_alerts:
            try:
                export_df = pd.DataFrame(filtered_alerts)
                csv = export_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export Filtered Alerts (CSV)",
                    data=csv,
                    file_name=f"threat_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"❌ Error exporting data: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== AI Analysis ==========
    elif menu == "🤖 AI Analysis":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 🤖 Gemini AI Threat Analysis Dashboard")
        
        # Import AI components
        try:
            from database.models import db_manager
            ai_analyses = db_manager.get_ai_analyses(limit=100)
            ai_stats = db_manager.get_ai_statistics()
            threat_signatures = db_manager.get_threat_signatures(limit=20)
            
            # AI Analysis Overview
            st.markdown("#### 📊 AI Analysis Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                create_metric_card("AI Analyses", ai_stats.get('total_ai_analyses', 0), "🧠")
            
            with col2:
                illegal_count = ai_stats.get('illegal_content_detected', 0)
                create_metric_card("Illegal Content", illegal_count, "⚠️")
            
            with col3:
                avg_confidence = ai_stats.get('avg_confidence_score', 0)
                create_metric_card("Avg Confidence", f"{avg_confidence:.1%}", "📊")
            
            with col4:
                active_signatures = ai_stats.get('active_threat_signatures', 0)
                create_metric_card("Threat Patterns", active_signatures, "🎯")
            
            # Threat Level Distribution
            st.markdown("#### 🎯 AI Threat Level Distribution")
            if ai_stats.get('ai_threat_levels'):
                threat_df = pd.DataFrame(list(ai_stats['ai_threat_levels'].items()), 
                                       columns=['Threat Level', 'Count'])
                
                fig = px.bar(
                    threat_df, 
                    x='Threat Level', 
                    y='Count',
                    color='Threat Level',
                    color_discrete_map={
                        'CRITICAL': '#dc2626',
                        'HIGH': '#ef4444',
                        'MEDIUM': '#f59e0b',
                        'LOW': '#22c55e',
                        'BENIGN': '#6b7280'
                    }
                )
                
                fig.update_layout(
                    font=dict(family="Rajdhani, sans-serif", color="white"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent AI Analyses
            st.markdown("#### 🔍 Recent AI Threat Analyses")
            
            # Filter controls
            col1, col2 = st.columns(2)
            with col1:
                threat_filter = st.selectbox("Filter by Threat Level:", 
                                           ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW", "BENIGN"])
            with col2:
                show_illegal_only = st.checkbox("Show only illegal content", value=False)
            
            # Apply filters
            filtered_analyses = ai_analyses.copy()
            if threat_filter != "All":
                filtered_analyses = [a for a in filtered_analyses if a.get('threat_level') == threat_filter]
            if show_illegal_only:
                filtered_analyses = [a for a in filtered_analyses if a.get('illegal_content_detected')]
            
            # Display AI analyses
            for analysis in filtered_analyses[:10]:  # Show top 10
                threat_level = analysis.get('threat_level', 'UNKNOWN')
                confidence = analysis.get('confidence_score', 0)
                illegal = analysis.get('illegal_content_detected', False)
                
                # Color coding based on threat level
                if threat_level in ['CRITICAL', 'HIGH']:
                    border_color = 'rgba(239, 68, 68, 0.3)'
                    bg_color = 'rgba(239, 68, 68, 0.1)'
                elif threat_level == 'MEDIUM':
                    border_color = 'rgba(251, 191, 36, 0.3)'
                    bg_color = 'rgba(251, 191, 36, 0.1)'
                else:
                    border_color = 'rgba(34, 197, 94, 0.3)'
                    bg_color = 'rgba(34, 197, 94, 0.1)'
                
                illegal_indicator = "⚠️ ILLEGAL CONTENT" if illegal else ""
                
                st.markdown(f"""
                    <div style="
                        background: {bg_color};
                        border: 1px solid {border_color};
                        border-radius: 15px;
                        padding: 1.5rem;
                        margin: 1rem 0;
                        backdrop-filter: blur(10px);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <span style="font-weight: 600; color: #e2e8f0;">🤖 AI Analysis - {threat_level}</span>
                            <span style="font-size: 0.9rem; color: #94a3b8;">📊 Confidence: {confidence:.1%}</span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <strong style="color: #e2e8f0;">🔗 URL:</strong> 
                            <a href="{analysis.get('url', '')}" target="_blank" style="color: #9333ea; text-decoration: none;">
                                {analysis.get('url', 'Unknown')}
                            </a>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <strong style="color: #e2e8f0;">📝 Summary:</strong> 
                            <span style="color: #cbd5e1;">{analysis.get('analysis_summary', 'No summary available')}</span>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <strong style="color: #e2e8f0;">🎯 Categories:</strong> 
                            <code style="background: rgba(0,0,0,0.3); padding: 0.2rem 0.5rem; border-radius: 5px; color: #9333ea;">
                                {', '.join(analysis.get('threat_categories', []))}
                            </code>
                        </div>
                        <div style="margin-bottom: 0.5rem;">
                            <strong style="color: #e2e8f0;">🔍 Indicators:</strong> 
                            <span style="color: #cbd5e1;">{', '.join(analysis.get('suspicious_indicators', [])[:3])}</span>
                        </div>
                        {f'<div style="color: #ef4444; font-weight: bold;">{illegal_indicator}</div>' if illegal else ''}
                    </div>
                """, unsafe_allow_html=True)
            
            # Threat Signatures Analysis
            st.markdown("#### 🎯 Active Threat Signatures")
            if threat_signatures:
                for sig in threat_signatures[:5]:  # Show top 5 signatures
                    st.markdown(f"""
                        <div style="
                            background: rgba(147, 51, 234, 0.1);
                            border: 1px solid rgba(147, 51, 234, 0.3);
                            border-radius: 10px;
                            padding: 1rem;
                            margin: 0.5rem 0;
                        ">
                            <strong>🔐 Signature:</strong> {sig.get('signature_hash', 'Unknown')}<br>
                            <strong>📊 Type:</strong> {sig.get('threat_type', 'Unknown')}<br>
                            <strong>🎯 Confidence:</strong> {sig.get('confidence_level', 0):.1%}<br>
                            <strong>📈 Occurrences:</strong> {sig.get('occurrence_count', 0)}
                        </div>
                    """, unsafe_allow_html=True)
            
            # AI Analysis Controls
            st.markdown("#### 🔧 AI Analysis Controls")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧠 Test AI Connection"):
                    try:
                        from ai.gemini_analyzer import gemini_analyzer
                        test_analysis = gemini_analyzer.analyze_content_sync(
                            url="test://example.onion",
                            title="Test Page",
                            content="This is a test page for AI analysis.",
                            keywords=["test"]
                        )
                        if test_analysis:
                            st.success("✅ AI Analysis is working correctly!")
                            st.info(f"Test result: {test_analysis.threat_level} threat level")
                        else:
                            st.error("❌ AI Analysis test failed")
                    except Exception as e:
                        st.error(f"❌ AI Connection failed: {e}")
            
            with col2:
                if st.button("📊 Generate AI Report"):
                    if ai_analyses:
                        try:
                            # Convert to ThreatAnalysis objects for report generation
                            from ai.gemini_analyzer import gemini_analyzer, ThreatAnalysis
                            analysis_objects = []
                            for analysis in ai_analyses[:50]:
                                threat_analysis = ThreatAnalysis(
                                    content_hash=analysis.get('content_hash', ''),
                                    threat_level=analysis.get('threat_level', 'LOW'),
                                    threat_categories=analysis.get('threat_categories', []),
                                    suspicious_indicators=analysis.get('suspicious_indicators', []),
                                    illegal_content_detected=analysis.get('illegal_content_detected', False),
                                    confidence_score=analysis.get('confidence_score', 0.0),
                                    analysis_summary=analysis.get('analysis_summary', ''),
                                    recommended_actions=analysis.get('recommended_actions', []),
                                    ai_reasoning=analysis.get('ai_reasoning', ''),
                                    timestamp=analysis.get('processed_at', '')
                                )
                                analysis_objects.append(threat_analysis)
                            
                            report = gemini_analyzer.generate_intelligence_report(analysis_objects)
                            
                            st.success("📊 Intelligence Report Generated")
                            
                            # Display report summary
                            st.json(report)
                            
                            # Download report
                            report_json = json.dumps(report, indent=2)
                            st.download_button(
                                label="📥 Download Full Report",
                                data=report_json,
                                file_name=f"ai_intelligence_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                        except Exception as e:
                            st.error(f"❌ Error generating report: {e}")
                    else:
                        st.warning("⚠️ No AI analyses available for report generation")
            
        except ImportError:
            st.error("❌ AI Analysis module not available. Please install required dependencies.")
        except Exception as e:
            st.error(f"❌ Error loading AI analysis data: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Live Monitoring ==========
    elif menu == "🧠 Live Monitoring":
        count = st_autorefresh(interval=30000, key="refresh_dashboard")  # every 30 seconds
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 🧠 Real-Time System Monitoring")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=False)
        
        if auto_refresh:
            st.rerun()
        
        try:
            logs = load_logs()
            
            # Display logs in a styled container
            st.markdown("#### 📋 Recent System Logs")
            log_text = "\n".join(logs[-50:])  # Show last 50 lines
            st.code(log_text, language="bash")
            
            # System status indicators
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status = "🟢 Active" if len(logs) > 1 else "🔴 Inactive"
                st.markdown(f"**Crawler Status:** {status}")
            
            with col2:
                st.markdown(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
                
                
                
                
                
            with col3:
                log_count = len([log for log in logs if log.strip()])
                st.markdown(f"**Log Entries:** {log_count}")
            
        except Exception as e:
            st.error(f"❌ Error loading monitoring data: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Real-time metrics
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("#### 📊 Real-Time Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            recent_alerts = len([a for a in valid_alerts if 'timestamp' in a])
            create_metric_card("Active Alerts", recent_alerts, "⚡")
        
        with col2:
            create_metric_card("Monitored Sites", len(visited), "🌐")
        
        with col3:
            create_metric_card("Threat Level", "MODERATE", "🔥")
        
        with col4:
            uptime = "99.2%"
            create_metric_card("System Uptime", uptime, "⏱️")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================
# Additional Utility Functions
# ============================
def format_timestamp(timestamp_str):
    """Format timestamp for better display"""
    try:
        dt = pd.to_datetime(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def get_domain_from_url(url):
    """Extract domain from URL"""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except:
        return url

def calculate_threat_score(keywords):
    """Calculate threat score based on keywords"""
    score = 0
    for keyword in keywords:
        severity = get_severity(keyword)
        if severity == "High":
            score += 10
        elif severity == "Medium":
            score += 5
        else:
            score += 1
    return min(score, 100)  # Cap at 100

# ============================
# Error Handling Wrapper
# ============================
def safe_execute(func, *args, **kwargs):
    """Safely execute functions with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        st.error(f"❌ Error in {func.__name__}: {e}")
        return None

# ============================
# Application Entry Point
# ============================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Critical application error: {e}")
        st.markdown("""
        ### 🚨 Application Error
        
        The dashboard encountered a critical error. Please:
        
        1. Check that all required data files exist
        2. Verify file permissions
        3. Ensure all dependencies are installed
        4. Try refreshing the page
        
        If the problem persists, contact your system administrator.
        """)
        
        # Show error details in expandable section
        with st.expander("🔍 Error Details"):
            st.code(str(e))
            
        # Emergency data reload
        if st.button("🔄 Emergency Reload"):
            st.cache_data.clear()
            st.rerun()
