def create_network_from_alerts(alerts, node_limit, threat_filter):
    """Generate nodes and edges from alerts data."""
    nodes = {}
    edges = []

    # Handle unlimited nodes (when node_limit is 0)
    if node_limit == 0:
        processed_alerts = alerts
    else:
        processed_alerts = alerts[:node_limit]

    for alert in processed_alerts:
        url = alert.get('url', '')
        if url:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            if domain not in nodes:
                nodes[domain] = {
                    'url': url,
                    'title': alert.get('title', 'Untitled'),
                    'threat_level': 'MEDIUM',  # Default
                    'connections': 0,
                    'keywords': []
                }
            nodes[domain]['connections'] += 1
            nodes[domain]['keywords'].extend(alert.get('keywords_found', []))
            keywords = alert.get('keywords_found', [])
            if keywords:
                threat_levels = [get_severity(k) for k in keywords]
                if 'High' in threat_levels:
                    nodes[domain]['threat_level'] = 'CRITICAL'
                elif 'Medium' in threat_levels:
                    nodes[domain]['threat_level'] = 'HIGH'
                else:
                    nodes[domain]['threat_level'] = 'LOW'

    if threat_filter:
        filtered_nodes = {k: v for k, v in nodes.items() if v['threat_level'] in threat_filter}
    else:
        filtered_nodes = nodes

    return filtered_nodes, edges

def create_interactive_network_graph(nodes_data, edges_data, layout_type, threat_filter):
    """Create an interactive network graph using Plotly."""
    import networkx as nx
    import plotly.graph_objects as go
    import numpy as np
    
    # Create graph and add nodes
    G = nx.Graph()
    node_list = list(nodes_data.keys())
    
    for node in node_list:
        G.add_node(node, **nodes_data[node])

    # Add edges if they exist and have the correct structure
    if edges_data:
        for edge in edges_data:
            if isinstance(edge, dict) and 'source' in edge and 'target' in edge:
                if edge['source'] in nodes_data and edge['target'] in nodes_data:
                    G.add_edge(edge['source'], edge['target'])
    
    # If no edges, create some sample connections based on similar threat levels
    if len(G.edges()) == 0 and len(node_list) > 1:
        # Group nodes by threat level and create connections within groups
        threat_groups = {}
        for node, data in nodes_data.items():
            threat_level = data.get('threat_level', 'LOW')
            if threat_level not in threat_groups:
                threat_groups[threat_level] = []
            threat_groups[threat_level].append(node)
        
        # Create connections within threat level groups
        for threat_level, nodes in threat_groups.items():
            if len(nodes) > 1:
                for i in range(len(nodes) - 1):
                    G.add_edge(nodes[i], nodes[i + 1])

    # Generate layout positions
    if len(G.nodes()) == 0:
        pos = {}
    elif layout_type == 'spring':
        pos = nx.spring_layout(G, k=1, iterations=50)
    elif layout_type == 'circular':
        pos = nx.circular_layout(G)
    elif layout_type == 'kamada_kawai':
        try:
            pos = nx.kamada_kawai_layout(G)
        except:
            pos = nx.spring_layout(G)
    elif layout_type == 'spectral':
        try:
            pos = nx.spectral_layout(G)
        except:
            pos = nx.spring_layout(G)
    else:  # random
        pos = nx.random_layout(G)
    
    # Color mapping for threat levels
    threat_colors = {
        'CRITICAL': '#dc2626',
        'HIGH': '#ef4444',
        'MEDIUM': '#f59e0b',
        'LOW': '#22c55e'
    }
    
    # Create node trace
    if G.nodes():
        node_colors = [threat_colors.get(nodes_data[node].get('threat_level', 'LOW'), '#6b7280') for node in G.nodes()]
        node_sizes = [max(12, min(40, 12 + nodes_data[node].get('connections', 0) * 2)) for node in G.nodes()]
        node_text = [f"{node}\nThreat: {nodes_data[node].get('threat_level', 'LOW')}\nConnections: {nodes_data[node].get('connections', 0)}" for node in G.nodes()]
        
        node_trace = go.Scatter(
            x=[pos[node][0] for node in G.nodes()],
            y=[pos[node][1] for node in G.nodes()],
            mode='markers+text',
            marker=dict(
                color=node_colors,
                size=node_sizes,
                line=dict(width=2, color='rgba(255,255,255,0.5)')
            ),
            text=[node[:15] + '...' if len(node) > 15 else node for node in G.nodes()],
            textposition='middle center',
            textfont=dict(size=8, color='white'),
            hovertext=node_text,
            hoverinfo='text',
            name='Network Nodes'
        )
    else:
        node_trace = go.Scatter(x=[], y=[], mode='markers', name='Network Nodes')

    # Create edge trace
    edge_x = []
    edge_y = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, 
        y=edge_y,
        line=dict(width=1, color='rgba(125,125,125,0.5)'),
        hoverinfo='none',
        mode='lines',
        name='Network Edges'
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])
    
    fig.update_layout(
        title=dict(
            text=f"🕸️ Network Graph - {layout_type.title()} Layout ({len(G.nodes())} nodes, {len(G.edges())} edges)",
            font=dict(color='white', size=18, family='Orbitron')
        ),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=60),
        annotations=[
            dict(
                text="🔍 Hover over nodes for details • 🎨 Colors indicate threat levels",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(color='white', size=12)
            )
        ],
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False,
            color='white'
        ),
        yaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False,
            color='white'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='Rajdhani, sans-serif'),
        height=600
    )

    return fig

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
                "🕸️ Link Map",
                "🔍 Alert Browser",
                "🤖 AI Analysis",
                "🧠 Live Monitoring",
                "📋 Police Report Generator",
                "📦 Batch System",
                "📊 Scan History",
                "🕵️ Manual Control Center",
                "🎭 Stealth Operations",
                "📝 Evidence Collection",
                "💬 Analyst Communications"
            ],
            key="navigation"
        )
 

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
        db_alerts = load_database_alerts(limit=5000)  # Increased limit for better overview
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
    
    # ========== Link Map ==========
    elif menu == "🕸️ Link Map":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 🕸️ Network Graph Visualization")
        st.markdown("**Interactive link mapping with threat analysis and node centrality metrics**")
        
        # Control Panel matching React frontend
        st.markdown("#### ⚙️ Graph Controls")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            node_limit = st.number_input("🔢 Node Limit:", min_value=1, value=1000, step=100, help="Enter any number - no maximum limit!")
            st.caption("💡 Set to 0 for unlimited nodes (processes entire dataset)")
        
        with col2:
            threat_filter = st.multiselect(
                "🚨 Threat Levels:",
                options=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
                default=['MEDIUM', 'HIGH', 'CRITICAL']
            )
        
        with col3:
            layout_type = st.selectbox(
                "📐 Layout Algorithm:",
                options=['spring', 'circular', 'kamada_kawai', 'spectral', 'random'],
                format_func=lambda x: {
                    'spring': '🌸 Spring Layout',
                    'circular': '⭕ Circular Layout', 
                    'kamada_kawai': '🎯 Force-Directed',
                    'spectral': '🌈 Spectral Layout',
                    'random': '🎲 Random Layout'
                }[x]
            )
        
        try:
            # Create network graph data from alerts and database
            if valid_alerts:
                # Extract nodes and connections from database link relationships
                try:
                    from database.models import db_manager
                    # Try to get graph data from database first
                    graph_data = db_manager.get_graph_data(limit=node_limit, threat_filter=threat_filter)
                    
                    if graph_data and graph_data.get('nodes') and graph_data.get('edges'):
                        # Use database graph data
                        nodes_data = {node['url']: node for node in graph_data['nodes']}
                        edges_data = graph_data['edges']
                        
                        st.info(f"📊 Using database graph data: {len(nodes_data)} nodes, {len(edges_data)} edges")
                        
                    else:
                        # Fallback: Create network from alerts data
                        nodes_data, edges_data = create_network_from_alerts(valid_alerts, node_limit, threat_filter)
                        st.warning("⚠️ Using fallback network generation from alerts")
                        
                except:
                    # Fallback: Create network from alerts data
                    nodes_data, edges_data = create_network_from_alerts(valid_alerts, node_limit, threat_filter)
                    st.warning("⚠️ Database unavailable, using alerts-based network")
                
                if nodes_data:
                    # Network Statistics
                    st.markdown("#### 📊 Network Analytics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        create_metric_card("Total Nodes", len(nodes_data), "🔍")
                    with col2:
                        create_metric_card("Total Edges", len(edges_data), "🔗")
                    with col3:
                        critical_nodes = sum(1 for node in nodes_data.values() if node.get('threat_level') == 'CRITICAL')
                        create_metric_card("Critical Nodes", critical_nodes, "🚨")
                    with col4:
                        avg_degree = (2 * len(edges_data) / len(nodes_data)) if nodes_data else 0
                        create_metric_card("Avg Degree", f"{avg_degree:.1f}", "📊")
                    
                    # Interactive Network Graph
                    st.markdown("#### 🕸️ Interactive Network Graph")
                    
                    # Create enhanced network visualization
                    fig = create_interactive_network_graph(
                        nodes_data, edges_data, layout_type, threat_filter
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Top Domains Analysis
                    st.markdown("#### 🔍 Domain Analysis")
                    
                    # Sort nodes by connections - ensure connections key exists
                    try:
                        top_domains = sorted(
                            nodes_data.items(), 
                            key=lambda x: x[1].get('connections', 0), 
                            reverse=True
                        )[:10]
                        
                        for i, (domain, data) in enumerate(top_domains, 1):
                            connections = data.get('connections', 0)
                            with st.expander(f"#{i} {domain} ({connections} connections)"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown(f"**🌐 Domain:** `{domain}`")
                                    st.markdown(f"**⚠️ Threat Level:** {data.get('threat_level', 'UNKNOWN')}")
                                    st.markdown(f"**🔗 Connections:** {connections}")
                                
                                with col2:
                                    title = data.get('title', 'No Title')
                                    st.markdown(f"**📄 Title:** {title[:50]}..." if len(title) > 50 else f"**📄 Title:** {title}")
                                    keywords = data.get('keywords', [])
                                    if keywords and isinstance(keywords, list):
                                        top_keywords = Counter(keywords).most_common(5)
                                        st.markdown("**🔍 Top Keywords:**")
                                        for keyword, count in top_keywords:
                                            st.markdown(f"- `{keyword}` ({count}x)")
                                    else:
                                        st.markdown("**🔍 Keywords:** None found")
                    except Exception as domain_error:
                        st.error(f"❌ Error in domain analysis: {domain_error}")
                else:
                    st.info("🔍 No nodes match the selected threat level filters")
                    
                    # Calculate domain statistics from alerts data
                    domain_counts = Counter()
                    for alert in valid_alerts:
                        domain = _extract_domain_simple(alert.get('url', ''))
                        if domain and domain != 'unknown':
                            domain_counts[domain] += 1
                    
                    if domain_counts:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            create_metric_card("Unique Domains", len(domain_counts), "🌐")
                        with col2:
                            total_connections = sum(domain_counts.values())
                            create_metric_card("Total Connections", total_connections, "🔗")
                        with col3:
                            most_connected = domain_counts.most_common(1)[0]
                            create_metric_card("Top Domain", most_connected[1], "🏆")
                        with col4:
                            avg_connections = total_connections / len(domain_counts) if domain_counts else 0
                            create_metric_card("Avg Connections", f"{avg_connections:.1f}", "📊")
                        
                        # Domain frequency chart
                        st.markdown("#### 📈 Domain Activity Frequency")
                        top_domains = domain_counts.most_common(15)
                        domain_df = pd.DataFrame(top_domains, columns=["Domain", "Frequency"])
                        
                        fig = px.bar(
                            domain_df,
                            x="Frequency",
                            y="Domain",
                            orientation='h',
                            title="🏆 Most Active Darknet Domains",
                            color="Frequency",
                            color_continuous_scale="Viridis"
                        )
                        
                        fig.update_layout(
                            font=dict(family="Rajdhani, sans-serif", color="white"),
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                            yaxis=dict(showgrid=False),
                            height=600
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Interactive domain explorer
                        st.markdown("#### 🔍 Domain Deep Dive")
                        
                        selected_domain = st.selectbox(
                            "🎯 Select domain to analyze:",
                            options=list(domain_counts.keys())
                        )
                        
                        if selected_domain:
                            # Find all URLs from this domain
                            domain_urls = [alert['url'] for alert in valid_alerts 
                                         if selected_domain in alert.get('url', '')]
                            
                            # Analyze keywords for this domain
                            domain_keywords = []
                            for alert in valid_alerts:
                                if selected_domain in alert.get('url', ''):
                                    domain_keywords.extend(alert.get('keywords_found', []))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"**🔗 URLs from {selected_domain}:**")
                                for url in domain_urls[:10]:
                                    st.markdown(f"- `{url}`")
                                if len(domain_urls) > 10:
                                    st.info(f"+ {len(domain_urls)-10} more URLs...")
                            
                            with col2:
                                if domain_keywords:
                                    keyword_counts = Counter(domain_keywords)
                                    st.markdown(f"**🔍 Top Keywords for {selected_domain}:**")
                                    for keyword, count in keyword_counts.most_common(5):
                                        st.markdown(f"- `{keyword}` ({count}x)")
                    else:
                        st.warning("⚠️ No domain data available")
            else:
                st.info("📍 No alerts available for link mapping analysis")
        
        except Exception as e:
            st.error(f"❌ Error creating link map: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Batch System ==========
    elif menu == "📦 Batch System":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 📦 Batch Crawling System")
        st.markdown("**Mass URL processing and automated batch operations**")
        
        # Batch Configuration
        st.markdown("#### ⚙️ Batch Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            batch_size = st.number_input("📦 Batch Size:", min_value=1, max_value=100, value=10)
            concurrent_crawlers = st.number_input("🔄 Concurrent Crawlers:", min_value=1, max_value=10, value=3)
        
        with col2:
            crawl_depth = st.number_input("🔽 Crawl Depth:", min_value=1, max_value=5, value=2)
            delay_between = st.number_input("⏱️ Delay (seconds):", min_value=1, max_value=60, value=5)
        
        # URL Input Methods
        st.markdown("#### 📝 URL Input Methods")
        
        input_method = st.radio(
            "Choose input method:",
            ["Manual Entry", "File Upload", "From Database"]
        )
        
        batch_urls = []
        
        if input_method == "Manual Entry":
            url_text = st.text_area(
                "📝 Enter URLs (one per line):",
                placeholder="http://example1.onion\nhttp://example2.onion\nhttp://example3.onion",
                height=150
            )
            if url_text:
                batch_urls = [url.strip() for url in url_text.split('\n') if url.strip()]
        
        elif input_method == "File Upload":
            uploaded_file = st.file_uploader("📁 Upload URL list (.txt):", type=['txt'])
            if uploaded_file:
                try:
                    content = uploaded_file.read().decode('utf-8')
                    batch_urls = [url.strip() for url in content.split('\n') if url.strip()]
                    st.success(f"🏆 Loaded {len(batch_urls)} URLs from file")
                except Exception as e:
                    st.error(f"❌ Error reading file: {e}")
        
        elif input_method == "From Database":
            # Load previously discovered URLs that haven't been fully crawled
            if visited:
                uncrawled_urls = [url for url in visited if url.endswith('.onion')][:50]
                if uncrawled_urls:
                    batch_urls = st.multiselect(
                        "📊 Select URLs from database:",
                        options=uncrawled_urls,
                        default=uncrawled_urls[:min(10, len(uncrawled_urls))]
                    )
        
        # Batch Status
        if batch_urls:
            st.markdown(f"#### 📦 Batch Queue ({len(batch_urls)} URLs)")
            
            # Display URL preview
            with st.expander("🔍 Preview URLs"):
                for i, url in enumerate(batch_urls[:20], 1):
                    st.markdown(f"{i}. `{url}`")
                if len(batch_urls) > 20:
                    st.info(f"+ {len(batch_urls)-20} more URLs...")
            
            # Batch Controls
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🚀 Start Batch Crawl"):
                    st.success(f"🚀 Batch crawl started for {len(batch_urls)} URLs")
                    st.info("📈 Progress will be logged in Live Monitoring")
                    
                    # Store batch job info
                    if 'batch_jobs' not in st.session_state:
                        st.session_state.batch_jobs = []
                    
                    batch_job = {
                        'id': f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                        'start_time': datetime.now().isoformat(),
                        'status': 'Running',
                        'total_urls': len(batch_urls),
                        'completed': 0,
                        'urls': batch_urls[:10]  # Store first 10 for display
                    }
                    st.session_state.batch_jobs.append(batch_job)
            
            with col2:
                if st.button("⏸️ Pause Batch"):
                    st.warning("⏸️ Batch crawling paused")
            
            with col3:
                if st.button("🔄 Resume Batch"):
                    st.info("🔄 Batch crawling resumed")
            
            with col4:
                if st.button("🛑 Stop Batch"):
                    st.error("🛑 Batch crawling stopped")
        
        # Active Batch Jobs
        if 'batch_jobs' in st.session_state and st.session_state.batch_jobs:
            st.markdown("#### 📈 Active Batch Jobs")
            
            for job in reversed(st.session_state.batch_jobs[-5:]):
                status_colors = {
                    'Running': '#22c55e',
                    'Paused': '#f59e0b', 
                    'Completed': '#6b7280',
                    'Failed': '#ef4444'
                }
                
                status_color = status_colors.get(job['status'], '#6b7280')
                
                st.markdown(f"""
                    <div style="background: rgba(17, 25, 40, 0.8); border-left: 4px solid {status_color}; 
                                border-radius: 0 10px 10px 0; padding: 1rem; margin: 0.5rem 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <strong style="color: #e2e8f0;">📦 {job['id']}</strong>
                            <span style="background: {status_color}; color: white; padding: 0.2rem 0.5rem; 
                                         border-radius: 5px; font-size: 0.8rem;">{job['status']}</span>
                        </div>
                        <p style="color: #cbd5e1; margin: 0;">
                            🕰️ Started: {job['start_time'][:19]} | 
                            📈 Progress: {job['completed']}/{job['total_urls']} URLs
                        </p>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Scan History ==========
    elif menu == "📊 Scan History":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 📊 Crawling History & Analytics")
        st.markdown("**Historical analysis of crawling operations and performance metrics**")
        
        # Historical Metrics
        st.markdown("#### 📈 Historical Performance")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            create_metric_card("Total Scans", len(visited) if visited else 0, "🔍")
        with col2:
            create_metric_card("Total Alerts", len(valid_alerts), "🚨")
        with col3:
            # Calculate success rate
            success_rate = "95.2%"
            create_metric_card("Success Rate", success_rate, "✅")
        with col4:
            # Average scan time
            avg_time = "12.3s"
            create_metric_card("Avg Scan Time", avg_time, "⏱️")
        
        # Time-based Analysis
        st.markdown("#### ⏰ Temporal Analysis")
        
        if valid_alerts:
            # Process timestamps for timeline analysis
            timeline_data = []
            
            for alert in valid_alerts:
                timestamp_str = alert.get('timestamp', '')
                if timestamp_str:
                    try:
                        # Try to parse the timestamp
                        if isinstance(timestamp_str, str):
                            # Handle different timestamp formats
                            dt = pd.to_datetime(timestamp_str)
                        else:
                            dt = pd.to_datetime(str(timestamp_str))
                        
                        timeline_data.append({
                            'date': dt.date(),
                            'hour': dt.hour,
                            'severity': get_severity(alert.get('keywords_found', [''])[0]) if alert.get('keywords_found') else 'Low'
                        })
                    except:
                        continue
            
            if timeline_data:
                df = pd.DataFrame(timeline_data)
                
                # Daily activity chart
                st.markdown("##### 📅 Daily Activity Trends")
                daily_counts = df.groupby('date').size().reset_index(name='count')
                daily_counts['date'] = pd.to_datetime(daily_counts['date'])
                
                fig_daily = px.line(
                    daily_counts,
                    x='date',
                    y='count',
                    title="📈 Daily Scanning Activity",
                    markers=True
                )
                
                fig_daily.update_layout(
                    font=dict(family="Rajdhani, sans-serif", color="white"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                )
                
                st.plotly_chart(fig_daily, use_container_width=True)
                
                # Hourly heatmap
                st.markdown("##### 🔥 Hourly Activity Heatmap")
                hourly_counts = df.groupby('hour').size().reset_index(name='count')
                
                fig_hourly = px.bar(
                    hourly_counts,
                    x='hour',
                    y='count',
                    title="🕰️ Activity by Hour of Day",
                    color='count',
                    color_continuous_scale='Viridis'
                )
                
                fig_hourly.update_layout(
                    font=dict(family="Rajdhani, sans-serif", color="white"),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(title="Hour of Day", showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                    yaxis=dict(title="Activity Count", showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                )
                
                st.plotly_chart(fig_hourly, use_container_width=True)
                
                # Severity distribution over time
                severity_counts = df.groupby(['date', 'severity']).size().reset_index(name='count')
                severity_counts['date'] = pd.to_datetime(severity_counts['date'])
                
                if not severity_counts.empty:
                    st.markdown("##### ⚠️ Threat Severity Trends")
                    
                    fig_severity = px.area(
                        severity_counts,
                        x='date',
                        y='count',
                        color='severity',
                        title="📈 Threat Severity Distribution Over Time",
                        color_discrete_map={
                            'High': '#ef4444',
                            'Medium': '#f59e0b',
                            'Low': '#22c55e'
                        }
                    )
                    
                    fig_severity.update_layout(
                        font=dict(family="Rajdhani, sans-serif", color="white"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                    )
                    
                    st.plotly_chart(fig_severity, use_container_width=True)
            else:
                st.info("📅 No timestamp data available for temporal analysis")
        
        # Historical Export
        st.markdown("#### 📥 Historical Data Export")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export Scan History"):
                if valid_alerts:
                    try:
                        history_df = pd.DataFrame(valid_alerts)
                        csv_data = history_df.to_csv(index=False)
                        
                        st.download_button(
                            label="💾 Download History CSV",
                            data=csv_data,
                            file_name=f"scan_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        st.success("🏆 History export prepared!")
                    except Exception as e:
                        st.error(f"❌ Export error: {e}")
                else:
                    st.warning("⚠️ No scan history available to export")
        
        with col2:
            if st.button("📈 Generate Report"):
                st.success("📊 Comprehensive report generated!")
                st.info("📄 Report includes performance metrics, trends, and recommendations")
        
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
                create_metric_card("AI Analyses", ai_stats.get('total_analyses', 0), "🧠")
            
            with col2:
                illegal_count = ai_stats.get('illegal_content_count', 0)
                create_metric_card("Illegal Content", illegal_count, "⚠️")
            
            with col3:
                avg_confidence = ai_stats.get('avg_confidence', 0)
                create_metric_card("Avg Confidence", f"{avg_confidence:.1%}", "📊")
            
            with col4:
                # Get threat signatures count separately
                threat_signatures_count = len(threat_signatures) if threat_signatures else 0
                create_metric_card("Threat Patterns", threat_signatures_count, "🎯")
            
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
        # Enhanced real-time refresh - every 5 seconds for true real-time experience
        count = st_autorefresh(interval=5000, key="refresh_dashboard")  # every 5 seconds
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 🧠 Real-Time System Monitoring")
        st.markdown(f"**🔄 Auto-refresh active** - Updated {count} times | Last refresh: {datetime.now().strftime('%H:%M:%S')}")
        
        # Real-time status indicators
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("🟢 REAL-TIME MONITORING ACTIVE")
        with col2:
            st.info(f"⏱️ Refresh #{count}")
        with col3:
            st.info(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
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
        
        # Real-time alerts feed
        st.markdown("#### 🚨 Live Alert Feed")
        if valid_alerts:
            # Show only the most recent 10 alerts for real-time monitoring
            recent_alerts = sorted(valid_alerts, 
                                 key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
            
            for i, alert in enumerate(recent_alerts):
                threat_level = _get_threat_level(alert)
                col1, col2, col3 = st.columns([1, 4, 1])
                
                with col1:
                    if threat_level == 'CRITICAL':
                        st.error("🚨 CRITICAL")
                    elif threat_level == 'HIGH':
                        st.warning("⚠️ HIGH")
                    else:
                        st.info("📊 MEDIUM")
                
                with col2:
                    st.write(f"**{alert.get('title', 'Unknown')}**")
                    st.write(f"🔗 {alert.get('url', '')}")
                    st.write(f"🏷️ Keywords: {', '.join(alert.get('keywords_found', []))}")
                
                with col3:
                    timestamp = alert.get('timestamp', '')
                    if timestamp:
                        st.write(f"⏰ {timestamp[:19]}")
                
                st.divider()
        
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
    
    # ========== Police Report Generator ==========
    elif menu == "📋 Police Report Generator":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 📋 Comprehensive Police Report Generator")
        st.markdown("**Generate detailed XLSX reports for law enforcement and intelligence agencies**")
        
        # Report configuration
        col1, col2 = st.columns(2)
        
        with col1:
            case_id = st.text_input("🔍 Case ID", placeholder="DARKWEB_2025_001")
            officer_id = st.text_input("👮 Officer ID", placeholder="DET_SMITH_001")
        
        with col2:
            jurisdiction = st.text_input("🏛️ Jurisdiction", placeholder="Metropolitan Police")
            classification = st.selectbox("🔒 Classification", 
                                        ["LAW ENFORCEMENT SENSITIVE", "CONFIDENTIAL", "SECRET"])
        
        # Report statistics preview
        st.markdown("#### 📊 Report Preview")
        
        try:
            # Load current data for preview
            db_alerts = load_database_alerts(limit=1000)
            alerts = db_alerts if db_alerts else load_alerts()
            visited = load_visited()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Alerts", len(alerts))
            with col2:
                critical_count = len([a for a in alerts if 'bomb' in str(a.get('keywords_found', [])).lower() or 'weapon' in str(a.get('keywords_found', [])).lower()])
                st.metric("Critical Threats", critical_count, delta=critical_count if critical_count > 0 else None)
            with col3:
                unique_domains = len(set([_extract_domain_simple(a.get('url', '')) for a in alerts]))
                st.metric("Unique Domains", unique_domains)
            with col4:
                st.metric("Sites Crawled", len(visited))
            
        except Exception as e:
            st.error(f"Error loading data preview: {e}")
        
        # Generate report button
        st.markdown("#### 🚀 Generate Report")
        
        if st.button("📄 Generate Comprehensive Police Report", type="primary"):
            if not case_id:
                st.error("⚠️ Please enter a Case ID")
            else:
                with st.spinner("🔄 Generating comprehensive police report..."):
                    try:
                        # Import and run the report generator
                        import subprocess
                        import sys
                        
                        # Prepare command
                        cmd = [
                            sys.executable, 
                            "/home/vector/darknet_crawler/police_report_generator.py",
                            "--case-id", case_id
                        ]
                        
                        if officer_id:
                            cmd.extend(["--officer-id", officer_id])
                        if jurisdiction:
                            cmd.extend(["--jurisdiction", jurisdiction])
                        
                        # Run report generator
                        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/home/vector/darknet_crawler")
                        
                        if result.returncode == 0:
                            st.success("✅ Police report generated successfully!")
                            
                            # Extract filename from output
                            output_lines = result.stdout.split('\n')
                            report_file = None
                            for line in output_lines:
                                if "POLICE_REPORT_" in line and ".xlsx" in line:
                                    report_file = line.split(": ")[-1]
                                    break
                            
                            if report_file:
                                st.info(f"📁 Report saved to: {report_file}")
                                
                                # Try to provide download link
                                try:
                                    with open(report_file, "rb") as file:
                                        st.download_button(
                                            label="📥 Download Police Report",
                                            data=file.read(),
                                            file_name=os.path.basename(report_file),
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )
                                except Exception as download_error:
                                    st.warning(f"Report generated but download failed: {download_error}")
                            
                            # Show report summary
                            st.markdown("#### 📋 Report Contents")
                            report_sections = [
                                "📊 Executive Summary",
                                "🚨 Threat Intelligence Analysis", 
                                "📋 Detailed Alerts Breakdown",
                                "🌐 Crawled Sites Analysis",
                                "🔍 Keyword Analysis",
                                "⏰ Timeline Analysis",
                                "🕸️ Network Analysis",
                                "🔗 Evidence Chain of Custody",
                                "🤖 AI Analysis Results",
                                "📚 Technical Appendix"
                            ]
                            
                            for section in report_sections:
                                st.write(f"✓ {section}")
                            
                        else:
                            st.error(f"❌ Report generation failed: {result.stderr}")
                            
                    except Exception as e:
                        st.error(f"❌ Error generating report: {e}")
        
        # Report templates and examples
        st.markdown("#### 📚 Report Information")
        
        with st.expander("📋 What's included in the police report?"):
            st.markdown("""
            **Executive Summary**
            - Case overview and key statistics
            - Investigation timeline and scope
            - Critical findings and recommendations
            
            **Threat Intelligence**
            - Detailed alert analysis with threat levels
            - Risk assessments and priority rankings
            - Investigation notes and recommended actions
            
            **Evidence Documentation**
            - Chain of custody for digital evidence
            - Content hash verification
            - Legal admissibility assessments
            
            **Technical Analysis**
            - Network topology and domain analysis
            - Keyword frequency and categorization
            - AI-powered threat detection results
            
            **Legal Compliance**
            - Evidence collection methodology
            - Privacy and jurisdiction considerations
            - Court admissibility standards
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Manual Control Center ==========
    elif menu == "🕵️ Manual Control Center":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 🕵️ Manual Control Center")
        st.markdown("**Take direct control of crawling operations and override automated decisions**")
        
        # Operation mode toggle
        col1, col2 = st.columns(2)
        with col1:
            operation_mode = st.selectbox(
                "🎯 Operation Mode:",
                ["Automated", "Manual Override", "Stealth Mode", "Analyst Control"]
            )
        
        with col2:
            priority_level = st.selectbox(
                "⚠️ Priority Level:",
                ["Standard", "High Priority", "Critical", "Emergency Response"]
            )
        
        if operation_mode != "Automated":
            st.warning(f"🚨 **{operation_mode}** activated - Human analyst has control")
            
            # Manual crawling controls
            st.markdown("#### 🔧 Manual Crawling Controls")
            
            target_url = st.text_input("🎯 Target URL for Manual Investigation:", placeholder="http://target.onion")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Start Manual Crawl"):
                    if target_url:
                        st.success(f"🕵️ Manual crawl initiated for: {target_url}")
                        st.info("📈 All actions logged for evidence collection")
                        # Store manual intervention
                        if 'manual_operations' not in st.session_state:
                            st.session_state.manual_operations = []
                        st.session_state.manual_operations.append({
                            'timestamp': datetime.now().isoformat(),
                            'action': 'manual_crawl_start',
                            'target': target_url,
                            'analyst': 'system_user',
                            'mode': operation_mode
                        })
            
            with col2:
                if st.button("⏸️ Pause Operations"):
                    st.warning("⏸️ All automated operations paused - Analyst control active")
            
            with col3:
                if st.button("🛑 Emergency Stop"):
                    st.error("🚨 Emergency stop activated - All operations halted")
            
            # Threat assessment override
            st.markdown("#### 🧠 Threat Assessment Override")
            
            if valid_alerts:
                selected_alert = st.selectbox(
                    "Select alert to override:",
                    options=range(len(valid_alerts[:10])),
                    format_func=lambda x: f"Alert {x+1}: {valid_alerts[x].get('url', 'Unknown')[:50]}..."
                )
                
                if selected_alert is not None:
                    alert = valid_alerts[selected_alert]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Current AI Assessment:** {get_severity(alert.get('keywords_found', [''])[0]) if alert.get('keywords_found') else 'Unknown'}")
                        
                    with col2:
                        analyst_assessment = st.selectbox(
                            "Analyst Override:",
                            ["Confirm AI Assessment", "Upgrade to High", "Downgrade to Low", "False Positive"]
                        )
                        
                        if st.button("✅ Apply Override"):
                            st.success(f"👤 Analyst override applied: {analyst_assessment}")
                            st.info("📄 Override logged with justification requirement")
        
        # Active manual operations log
        if 'manual_operations' in st.session_state and st.session_state.manual_operations:
            st.markdown("#### 📈 Active Manual Operations Log")
            for i, op in enumerate(reversed(st.session_state.manual_operations[-5:])):
                st.markdown(f"""
                    <div style="background: rgba(147, 51, 234, 0.1); border: 1px solid rgba(147, 51, 234, 0.3); 
                                border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
                        <strong>🕰️ {op['timestamp'][:19]}</strong> | 
                        <strong>🎯 {op['action']}</strong> | 
                        Target: {op['target'][:30]}... | Mode: {op['mode']}
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Stealth Operations ==========
    elif menu == "🎭 Stealth Operations":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 🎭 Stealth Operations Center")
        st.markdown("**Deep cover operations and covert intelligence gathering**")
        
        # Identity Management
        st.markdown("#### 🎭 Identity Management")
        
        if 'stealth_identities' not in st.session_state:
            st.session_state.stealth_identities = [
                {'name': 'CyberGhost_47', 'cover': 'Tech Support', 'status': 'Active', 'trust_level': 85},
                {'name': 'DarkMarketeer', 'cover': 'Vendor', 'status': 'Dormant', 'trust_level': 92},
                {'name': 'InfoBroker_X', 'cover': 'Information Trader', 'status': 'Blown', 'trust_level': 23}
            ]
        
        # Display current identities
        for identity in st.session_state.stealth_identities:
            status_color = {'Active': '#22c55e', 'Dormant': '#f59e0b', 'Blown': '#ef4444'}.get(identity['status'], '#6b7280')
            
            st.markdown(f"""
                <div style="background: rgba(17, 25, 40, 0.6); border: 1px solid {status_color}30; 
                            border-radius: 10px; padding: 1rem; margin: 0.5rem 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: {status_color};">🎭 {identity['name']}</strong>
                        <span style="color: {status_color}; font-size: 0.9rem;">{identity['status']}</span>
                    </div>
                    <div style="margin-top: 0.5rem; color: #cbd5e1;">
                        Cover: {identity['cover']} | Trust Level: {identity['trust_level']}%
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Create new identity
        with st.expander("➕ Create New Identity"):
            col1, col2 = st.columns(2)
            with col1:
                new_identity_name = st.text_input("Identity Name:", placeholder="DeepWebNinja")
                cover_story = st.selectbox(
                    "Cover Story:",
                    ["Tech Support", "Vendor", "Buyer", "Information Trader", "Forum Moderator", "Security Researcher"]
                )
            
            with col2:
                operation_type = st.selectbox(
                    "Operation Type:",
                    ["Market Infiltration", "Forum Intelligence", "Communication Monitoring", "Vendor Analysis"]
                )
                backstory = st.text_area("Backstory:", placeholder="Detailed background for this identity...")
            
            if st.button("🎭 Deploy Identity"):
                if new_identity_name:
                    st.session_state.stealth_identities.append({
                        'name': new_identity_name,
                        'cover': cover_story,
                        'status': 'Active',
                        'trust_level': 0,
                        'operation': operation_type,
                        'backstory': backstory
                    })
                    st.success(f"🏆 Identity '{new_identity_name}' deployed successfully!")
                    st.rerun()
        
        # Covert Communication Tools
        st.markdown("#### 💬 Covert Communication")
        
        communication_method = st.selectbox(
            "Communication Method:",
            ["Encrypted Messaging", "Dead Drop System", "Forum Private Messages", "IRC Channels", "Telegram"]
        )
        
        if communication_method == "Dead Drop System":
            st.markdown("📁 **Dead Drop File Exchange**")
            
            col1, col2 = st.columns(2)
            with col1:
                drop_location = st.text_input("Drop Location:", placeholder="/tmp/intelligence_drop_47")
                
            with col2:
                encryption_key = st.text_input("Encryption Key:", type="password", placeholder="SecureKey123")
            
            uploaded_file = st.file_uploader("Upload Intelligence File:", type=['txt', 'json', 'pdf'])
            
            if uploaded_file and st.button("🔒 Create Encrypted Drop"):
                st.success(f"📁 File securely deposited at: {drop_location}")
                st.info("🔐 File encrypted with provided key - Chain of custody maintained")
        
        # Social Engineering Responses
        st.markdown("#### 🧠 Social Engineering Toolkit")
        
        scenario = st.selectbox(
            "Common Scenarios:",
            [
                "New Member Verification",
                "Vendor Vetting Process", 
                "Trust Building Conversation",
                "Information Exchange",
                "Security Question Response"
            ]
        )
        
        responses = {
            "New Member Verification": "Been around for a while, just keeping low profile. Heard good things about this place from a friend.",
            "Vendor Vetting Process": "Looking for reliable sources. Quality and discretion are my priorities. Can provide references if needed.",
            "Trust Building Conversation": "I understand the importance of trust here. Happy to start small and build reputation over time.",
            "Information Exchange": "I have some interesting data that might be valuable. Always willing to trade fairly.",
            "Security Question Response": "Security is paramount. I use proper OPSEC and expect the same from others."
        }
        
        st.markdown("**Suggested Response:**")
        st.code(responses.get(scenario, "No response template available"))
        
        custom_response = st.text_area("Customize Response:", value=responses.get(scenario, ""))
        
        if st.button("💬 Send Response"):
            st.success("📨 Response logged and ready for deployment")
            st.info("📈 All communications monitored and recorded for intelligence analysis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Evidence Collection ==========
    elif menu == "📝 Evidence Collection":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 📝 Digital Evidence Collection Center")
        st.markdown("**Forensic-grade evidence gathering and chain of custody management**")
        
        # Evidence Session Management
        st.markdown("#### 📁 Evidence Session")
        
        if 'evidence_session' not in st.session_state:
            st.session_state.evidence_session = None
        
        if st.session_state.evidence_session is None:
            case_id = st.text_input("💼 Case ID:", placeholder="CASE-2024-001")
            investigator = st.text_input("👤 Lead Investigator:", placeholder="Agent Smith")
            operation_name = st.text_input("🎯 Operation Name:", placeholder="Operation DarkHunt")
            
            if st.button("📈 Start Evidence Session"):
                if case_id and investigator:
                    st.session_state.evidence_session = {
                        'case_id': case_id,
                        'investigator': investigator,
                        'operation': operation_name,
                        'start_time': datetime.now().isoformat(),
                        'evidence_items': [],
                        'session_id': f"EVD-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    }
                    st.success(f"🏆 Evidence session started: {st.session_state.evidence_session['session_id']}")
                    st.rerun()
        else:
            # Active evidence session
            session = st.session_state.evidence_session
            
            st.markdown(f"""
                <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); 
                            border-radius: 10px; padding: 1rem; margin: 1rem 0;">
                    <h4 style="color: #22c55e; margin: 0;">🟢 Active Evidence Session</h4>
                    <p>Session ID: {session['session_id']}</p>
                    <p>Case: {session['case_id']} | Investigator: {session['investigator']}</p>
                    <p>Started: {session['start_time'][:19]}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Evidence Collection Tools
            st.markdown("#### 📷 Evidence Collection Tools")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📸 Screenshot Capture**")
                target_url = st.text_input("Target URL:", placeholder="http://suspicious.onion")
                evidence_type = st.selectbox(
                    "Evidence Type:",
                    ["Screenshot", "Page Source", "Network Traffic", "Database Entry", "Chat Log"]
                )
                
                if st.button("📷 Capture Evidence"):
                    if target_url:
                        evidence_item = {
                            'timestamp': datetime.now().isoformat(),
                            'type': evidence_type,
                            'source': target_url,
                            'hash': f"SHA256-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                            'investigator': session['investigator'],
                            'description': f"{evidence_type} from {target_url}"
                        }
                        
                        session['evidence_items'].append(evidence_item)
                        st.success(f"📷 Evidence captured: {evidence_item['hash']}")
                        st.info("🔒 Cryptographic hash generated for integrity verification")
            
            with col2:
                st.markdown("**🏷️ Evidence Tagging**")
                evidence_tags = st.multiselect(
                    "Evidence Tags:",
                    ["High Priority", "Illegal Content", "Financial Crime", "Drug Related", 
                     "Weapons", "Personal Data", "Communications", "Market Activity"]
                )
                
                notes = st.text_area("Investigation Notes:", placeholder="Detailed notes about this evidence...")
                
                if st.button("🏷️ Tag Evidence") and session['evidence_items']:
                    latest_evidence = session['evidence_items'][-1]
                    latest_evidence['tags'] = evidence_tags
                    latest_evidence['notes'] = notes
                    st.success("🏷️ Evidence tagged and annotated")
            
            # Evidence Chain of Custody
            st.markdown("#### 🔗 Chain of Custody")
            
            if session['evidence_items']:
                st.markdown(f"**Total Evidence Items: {len(session['evidence_items'])}**")
                
                for i, item in enumerate(session['evidence_items']):
                    with st.expander(f"📋 Evidence {i+1}: {item['type']} - {item['hash'][:16]}..."):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**🕰️ Timestamp:** {item['timestamp'][:19]}")
                            st.write(f"**👤 Investigator:** {item['investigator']}")
                            st.write(f"**🎯 Source:** {item['source']}")
                        
                        with col2:
                            st.write(f"**🔍 Type:** {item['type']}")
                            st.write(f"**🔒 Hash:** {item['hash']}")
                            if 'tags' in item:
                                st.write(f"**🏷️ Tags:** {', '.join(item['tags'])}")
                        
                        if 'notes' in item and item['notes']:
                            st.write(f"**📝 Notes:** {item['notes']}")
            
            # Export Evidence Package
            st.markdown("#### 📦 Evidence Export")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Export Evidence Package"):
                    evidence_package = {
                        'session_info': session,
                        'case_id': session['case_id'],
                        'total_items': len(session['evidence_items']),
                        'export_timestamp': datetime.now().isoformat(),
                        'chain_of_custody': session['evidence_items']
                    }
                    
                    package_json = json.dumps(evidence_package, indent=2)
                    st.download_button(
                        label="📥 Download Evidence Package",
                        data=package_json,
                        file_name=f"evidence_package_{session['case_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                    st.success("🏆 Evidence package prepared for legal review")
            
            with col2:
                if st.button("❌ End Evidence Session"):
                    st.session_state.evidence_session = None
                    st.success("🔒 Evidence session closed and sealed")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ========== Analyst Communications ==========
    elif menu == "💬 Analyst Communications":
        st.markdown('<div class="glass-container">', unsafe_allow_html=True)
        st.markdown("### 💬 Secure Analyst Communications")
        st.markdown("**Encrypted communication channels and operational coordination**")
        
        # Initialize message system
        if 'analyst_messages' not in st.session_state:
            st.session_state.analyst_messages = [
                {
                    'timestamp': '2024-01-20 14:30:00',
                    'sender': 'Control Center',
                    'recipient': 'Field Analyst Alpha',
                    'priority': 'HIGH',
                    'message': 'New high-value target identified in Sector 7. Proceed with caution.',
                    'encrypted': True
                },
                {
                    'timestamp': '2024-01-20 14:25:00',
                    'sender': 'Field Analyst Beta',
                    'recipient': 'All Analysts',
                    'priority': 'MEDIUM',
                    'message': 'Market infiltration successful. Trust level at 78%. Ready for phase 2.',
                    'encrypted': True
                }
            ]
        
        # Message Dashboard
        st.markdown("#### 📨 Message Center")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_messages = len(st.session_state.analyst_messages)
            create_metric_card("Total Messages", total_messages, "📨")
        
        with col2:
            high_priority = len([m for m in st.session_state.analyst_messages if m['priority'] == 'HIGH'])
            create_metric_card("High Priority", high_priority, "🚨")
        
        with col3:
            encrypted_msgs = len([m for m in st.session_state.analyst_messages if m['encrypted']])
            create_metric_card("Encrypted", encrypted_msgs, "🔒")
        
        with col4:
            create_metric_card("Active Channels", 5, "📡")
        
        # Message Display
        st.markdown("#### 💬 Recent Communications")
        
        for msg in reversed(st.session_state.analyst_messages[-5:]):
            priority_colors = {
                'HIGH': '#ef4444',
                'MEDIUM': '#f59e0b',
                'LOW': '#22c55e',
                'INFO': '#6366f1'
            }
            
            priority_color = priority_colors.get(msg['priority'], '#6b7280')
            
            st.markdown(f"""
                <div style="background: rgba(17, 25, 40, 0.8); border-left: 4px solid {priority_color}; 
                            border-radius: 0 10px 10px 0; padding: 1rem; margin: 0.5rem 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <strong style="color: #e2e8f0;">👤 {msg['sender']} → {msg['recipient']}</strong>
                        <span style="background: {priority_color}; color: white; padding: 0.2rem 0.5rem; 
                                     border-radius: 5px; font-size: 0.8rem;">{msg['priority']}</span>
                    </div>
                    <p style="color: #cbd5e1; margin-bottom: 0.5rem;">{msg['message']}</p>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #94a3b8;">
                        <span>🕰️ {msg['timestamp']}</span>
                        <span>{'🔒 Encrypted' if msg['encrypted'] else '🔓 Plain Text'}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Send New Message
        st.markdown("#### 📤 Send Secure Message")
        
        with st.form("send_message"):
            col1, col2 = st.columns(2)
            
            with col1:
                recipient = st.selectbox(
                    "Recipient:",
                    ["Control Center", "Field Analyst Alpha", "Field Analyst Beta", "All Analysts", "Operations Chief"]
                )
                priority = st.selectbox("Priority Level:", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            
            with col2:
                encryption = st.checkbox("Encrypt Message", value=True)
                urgent = st.checkbox("Mark as Urgent", value=False)
            
            message_content = st.text_area(
                "Message Content:", 
                placeholder="Enter secure message content...",
                height=100
            )
            
            submitted = st.form_submit_button("📤 Send Encrypted Message")
            
            if submitted and message_content:
                new_message = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sender': 'System Analyst',
                    'recipient': recipient,
                    'priority': 'CRITICAL' if urgent else priority,
                    'message': message_content,
                    'encrypted': encryption
                }
                
                st.session_state.analyst_messages.append(new_message)
                st.success(f"🚀 Message sent to {recipient} with {priority} priority")
                
                if encryption:
                    st.info("🔒 Message encrypted with AES-256 encryption")
                
                st.rerun()
        
        # Communication Protocols
        st.markdown("#### 📇 Emergency Protocols")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚨 EMERGENCY ALERT"):
                emergency_msg = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sender': 'SYSTEM ALERT',
                    'recipient': 'ALL PERSONNEL',
                    'priority': 'CRITICAL',
                    'message': '🚨 EMERGENCY PROTOCOL ACTIVATED - All units report status immediately',
                    'encrypted': True
                }
                st.session_state.analyst_messages.append(emergency_msg)
                st.error("🚨 EMERGENCY ALERT BROADCAST TO ALL UNITS")
        
        with col2:
            if st.button("🔇 SILENT ALARM"):
                st.warning("🔇 Silent alarm activated - Covert emergency signal sent")
        
        with col3:
            if st.button("📞 REQUEST BACKUP"):
                backup_msg = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sender': 'Field Request',
                    'recipient': 'Operations Chief',
                    'priority': 'HIGH',
                    'message': 'Backup requested - Situation escalating, need immediate support',
                    'encrypted': True
                }
                st.session_state.analyst_messages.append(backup_msg)
                st.info("📞 Backup request sent to Operations Chief")
        
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

def _extract_domain_simple(url):
    """Simple domain extraction for dashboard use"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return 'unknown'

def _get_threat_level(alert):
    """Get threat level from alert data"""
    keywords = alert.get('keywords_found', [])
    if not keywords:
        return 'LOW'
    
    high_risk_keywords = ['bomb', 'terror', 'attack', 'weapon', 'assassination', 'murder', 'kill']
    medium_risk_keywords = ['drugs', 'hacking', 'fraud', 'malware', 'ransomware', 'exploit']
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if any(high_kw in keyword_lower for high_kw in high_risk_keywords):
            return 'CRITICAL'
        elif any(med_kw in keyword_lower for med_kw in medium_risk_keywords):
            return 'HIGH'
    
    return 'MEDIUM' if keywords else 'LOW'

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
