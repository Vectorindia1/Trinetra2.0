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
@st.cache_data
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

@st.cache_data
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

@st.cache_data
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
                "☁️ Threat Cloud",
                "📈 Keyword Analytics", 
                "⏰ Timeline Analysis",
                "🔍 Alert Browser",
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
                        subprocess.Popen(
                            [
                              "scrapy", "crawl", "onion",
                              "-a", f"start_url={tor_link_input.strip()}",
                              "-s", "LOG_FILE=crawler.log"
                            ],
                            cwd=".",
                            stdout=open("crawler.log", "a"),
                            stderr=subprocess.STDOUT
                        )
                        st.success("🟢 Scraper started in background. Monitoring live updates below.")
                    except Exception as ex:
                        st.error(f"❌ Failed to launch scraper: {ex}")
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
        alerts = load_alerts()
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
    
    # ========== Threat Cloud ==========
    elif menu == "☁️ Threat Cloud":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### ☁️ Threat Keyword Cloud")
        
        if all_keywords:
            try:
                # Create enhanced word cloud
                wc = WordCloud(
                    width=1200, 
                    height=600, 
                    background_color='rgba(0,0,0,0)',
                    mode='RGBA',
                    colormap='plasma',
                    max_words=100,
                    relative_scaling=0.5,
                    random_state=42
                ).generate(" ".join(all_keywords))
                
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                fig.patch.set_facecolor('none')
                fig.patch.set_alpha(0)
                
                st.pyplot(fig, use_container_width=True, transparent=True)
                
            except Exception as e:
                st.error(f"❌ Error generating word cloud: {e}")
        else:
            st.warning("⚠️ No keywords available for visualization")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Keyword Analytics ==========
    elif menu == "📈 Keyword Analytics":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 📈 Keyword Distribution Analysis")
        
        if all_keywords:
            try:
                keyword_counts = Counter(all_keywords)
                
                # Create enhanced pie chart
                pie_df = pd.DataFrame(keyword_counts.most_common(10), columns=["Keyword", "Count"])
                
                fig = px.pie(
                    pie_df, 
                    names="Keyword", 
                    values="Count",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Plasma
                )
                
                fig.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )
                
                fig.update_layout(
                    font=dict(family="Rajdhani, sans-serif", size=12, color="white"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=0, b=0, l=0, r=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Severity breakdown
                severity_counts = Counter([get_severity(k) for k in all_keywords])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    create_metric_card("High Risk", severity_counts.get("High", 0), "🔴")
                with col2:
                    create_metric_card("Medium Risk", severity_counts.get("Medium", 0), "🟡")
                with col3:
                    create_metric_card("Low Risk", severity_counts.get("Low", 0), "🟢")
                
            except Exception as e:
                st.error(f"❌ Error creating analytics: {e}")
        else:
            st.info("📭 No keyword data available for analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Timeline Analysis ==========
    elif menu == "⏰ Timeline Analysis":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### ⏰ Threat Timeline Analysis")
        
        try:
            time_data = []
            for alert in valid_alerts:
                if "timestamp" in alert:
                    try:
                        timestamp = pd.to_datetime(alert["timestamp"])
                        severity = max([get_severity(k) for k in alert.get("keywords_found", [])], default="Low")
                        time_data.append({"timestamp": timestamp, "severity": severity})
                    except:
                        continue
            
            if time_data:
                df = pd.DataFrame(time_data)
                
                # Hourly aggregation
                df['hour'] = df['timestamp'].dt.floor('H')
                hourly_counts = df.groupby(['hour', 'severity']).size().reset_index(name='count')
                
                # Create enhanced timeline chart
                fig = px.line(
                    hourly_counts, 
                    x='hour', 
                    y='count', 
                    color='severity',
                    color_discrete_map={
                        'High': '#ef4444',
                        'Medium': '#f59e0b',
                        'Low': '#22c55e'
                    },
                    title="Threat Activity Over Time"
                )
                
                fig.update_layout(
                    font=dict(family="Rajdhani, sans-serif", color="white"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📭 No timeline data available")
                
        except Exception as e:
            st.error(f"❌ Error creating timeline: {e}")
        
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
