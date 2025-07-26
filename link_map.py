"""
Link Map Visualization Module
Creates an interactive graph view similar to Obsidian's graph view
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import json
from datetime import datetime
from database.models import db_manager
import numpy as np

def create_link_map_tab():
    """Create the link map visualization tab"""
    st.header("🕸️ Link Map Explorer")
    st.markdown("*Visualize the web of connections between discovered sites*")
    
    # Control panels
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        node_limit = st.slider("Max Nodes", min_value=50, max_value=2000, value=500, step=50)
        
    with col2:
        threat_filter = st.multiselect(
            "Threat Levels",
            options=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
            default=['MEDIUM', 'HIGH', 'CRITICAL']
        )
    
    with col3:
        layout_type = st.selectbox(
            "Layout",
            options=['spring', 'circular', 'kamada_kawai', 'spectral', 'random']
        )
    
    with col4:
        if st.button("🔄 Refresh Graph", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # Load and display graph data
    try:
        graph_data = get_graph_data(node_limit, threat_filter)
        
        if graph_data['nodes']:
            # Display statistics
            display_graph_statistics(graph_data)
            
            # Create and display the graph
            fig = create_network_graph(graph_data, layout_type)
            st.plotly_chart(fig, use_container_width=True, key="link_map_graph")
            
            # Display detailed tables
            display_graph_tables(graph_data)
            
        else:
            st.info("🔍 No graph data available. Start crawling to build the link map!")
            
    except Exception as e:
        st.error(f"❌ Error loading graph data: {e}")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_graph_data(node_limit, threat_filter):
    """Get graph data from database"""
    try:
        # Update centrality scores before fetching
        db_manager.calculate_centrality_scores()
        
        # Get graph data with filters
        graph_data = db_manager.get_graph_data(
            limit=node_limit,
            threat_filter=threat_filter if threat_filter else None
        )
        
        return graph_data
        
    except Exception as e:
        st.error(f"Error fetching graph data: {e}")
        return {'nodes': [], 'edges': [], 'stats': {}}

def display_graph_statistics(graph_data):
    """Display graph statistics in an attractive layout"""
    stats = graph_data['stats']
    
    # Main stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🔗 Total Nodes",
            value=stats.get('total_nodes', 0),
            help="Total number of discovered pages"
        )
    
    with col2:
        st.metric(
            label="🕸️ Total Edges", 
            value=stats.get('total_edges', 0),
            help="Total number of link relationships"
        )
    
    with col3:
        st.metric(
            label="🔗 Internal Links",
            value=stats.get('internal_links', 0),
            help="Links between .onion sites"
        )
    
    with col4:
        st.metric(
            label="🌐 External Links",
            value=stats.get('external_links', 0),
            help="Links to external sites"
        )
    
    # Additional statistics
    try:
        link_stats = db_manager.get_link_map_statistics()
        
        if link_stats.get('nodes_by_threat'):
            st.subheader("📊 Threat Level Distribution")
            
            threat_df = pd.DataFrame(
                list(link_stats['nodes_by_threat'].items()),
                columns=['Threat Level', 'Count']
            )
            
            # Color map for threats
            color_map = {
                'LOW': '#22c55e',
                'MEDIUM': '#f59e0b', 
                'HIGH': '#ef4444',
                'CRITICAL': '#dc2626'
            }
            
            fig_threat = px.pie(
                threat_df,
                values='Count',
                names='Threat Level',
                color='Threat Level',
                color_discrete_map=color_map,
                title="Nodes by Threat Level"
            )
            fig_threat.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_threat, use_container_width=True)
            
    except Exception as e:
        st.warning(f"Could not load additional statistics: {e}")

def create_network_graph(graph_data, layout_type='spring'):
    """Create interactive network graph using plotly with Obsidian-style aesthetics"""
    
    if not graph_data['nodes'] or not graph_data['edges']:
        # Create empty graph with enhanced styling
        fig = go.Figure()
        fig.add_annotation(
            text="🔍 No network data available<br><i>Start crawling to build connections</i>",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=18, color="#64748b")
        )
        fig.update_layout(
            plot_bgcolor='#0f172a',
            paper_bgcolor='#0f172a',
            showlegend=False,
            height=700
        )
        return fig
    
    # Create NetworkX graph for layout calculation
    G = nx.Graph()
    
    # Add nodes with weights
    for node in graph_data['nodes']:
        weight = node.get('centrality_score', 0) + (node.get('incoming_links', 0) * 0.1)
        G.add_node(
            node['url'], 
            weight=weight,
            **{k: v for k, v in node.items() if k != 'url'}
        )
    
    # Add edges with weights
    for edge in graph_data['edges']:
        weight = edge.get('occurrence_count', 1)
        G.add_edge(
            edge['source_url'], 
            edge['target_url'],
            weight=weight,
            **{k: v for k, v in edge.items() if k not in ['source_url', 'target_url']}
        )
    
    # Enhanced layout calculation with better positioning
    try:
        if layout_type == 'spring':
            pos = nx.spring_layout(G, k=5, iterations=100, seed=42, weight='weight')
        elif layout_type == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(G, weight='weight')
        elif layout_type == 'circular':
            # Sort nodes by centrality for better circular arrangement
            nodes_by_centrality = sorted(G.nodes(), key=lambda x: G.nodes[x].get('weight', 0), reverse=True)
            pos = nx.circular_layout(nodes_by_centrality)
        elif layout_type == 'spectral':
            pos = nx.spectral_layout(G, weight='weight')
        else:
            pos = nx.random_layout(G, seed=42)
    except:
        # Fallback to enhanced spring layout
        pos = nx.spring_layout(G, k=5, iterations=100, seed=42)
    
    # Scale positions for better spacing
    pos = {node: (coord[0] * 2, coord[1] * 2) for node, coord in pos.items()}
    
    # Extract coordinates
    x_nodes = [pos[node][0] for node in G.nodes()]
    y_nodes = [pos[node][1] for node in G.nodes()]
    
    # Enhanced edge visualization with curved lines and varying thickness
    edge_traces = []
    
    for edge_data in graph_data['edges']:
        source = edge_data['source_url']
        target = edge_data['target_url']
        
        if source in pos and target in pos:
            x0, y0 = pos[source]
            x1, y1 = pos[target]
            
            # Calculate curved path for edges
            mid_x = (x0 + x1) / 2 + np.random.normal(0, 0.1)  # Add slight randomness
            mid_y = (y0 + y1) / 2 + np.random.normal(0, 0.1)
            
            # Edge thickness based on occurrence count
            thickness = min(max(edge_data.get('occurrence_count', 1) * 0.5, 0.3), 3.0)
            
            # Edge color based on relationship type
            if edge_data.get('is_external', False):
                edge_color = 'rgba(99, 102, 241, 0.4)'  # Blue for external
            else:
                edge_color = 'rgba(147, 51, 234, 0.6)'  # Purple for internal
            
            # Create smooth curved edge
            edge_trace = go.Scatter(
                x=[x0, mid_x, x1],
                y=[y0, mid_y, y1],
                mode='lines',
                line=dict(
                    width=thickness,
                    color=edge_color,
                    shape='spline',
                    smoothing=1.0
                ),
                hoverinfo='none',
                showlegend=False,
                opacity=0.7
            )
            edge_traces.append(edge_trace)
    
    # Prepare node data with enhanced styling
    node_urls = list(G.nodes())
    node_data = {node['url']: node for node in graph_data['nodes']}
    
    # Enhanced color scheme inspired by Obsidian
    threat_colors = {
        'LOW': '#10b981',      # Emerald
        'MEDIUM': '#f59e0b',   # Amber  
        'HIGH': '#ef4444',     # Red
        'CRITICAL': '#dc2626'  # Dark red
    }
    
    # Prepare node visual properties
    node_colors = []
    node_sizes = []
    node_labels = []
    hover_texts = []
    
    for url in node_urls:
        node_info = node_data.get(url, {})
        
        # Color based on threat level
        threat = node_info.get('threat_level', 'LOW')
        color = threat_colors.get(threat, '#64748b')
        node_colors.append(color)
        
        # Size based on centrality and connections
        centrality = node_info.get('centrality_score', 0)
        incoming = node_info.get('incoming_links', 0)
        outgoing = node_info.get('outgoing_links', 0)
        
        # Calculate node size (12-35 range)
        base_size = 12
        centrality_bonus = centrality * 8
        connection_bonus = (incoming + outgoing) * 0.5
        size = min(max(base_size + centrality_bonus + connection_bonus, 12), 35)
        node_sizes.append(size)
        
        # Node labels - extract domain/title
        title = node_info.get('title', 'Untitled')
        if len(title) > 15:
            # Try to extract meaningful part
            if '.onion' in url:
                domain_part = url.split('.onion')[0].split('//')[-1][:8]
                label = domain_part.upper()
            else:
                label = title[:12] + '...'
        else:
            label = title
        
        node_labels.append(label)
        
        # Enhanced hover text
        page_size = node_info.get('page_size', 0)
        last_crawled = node_info.get('last_crawled', 'Never')
        
        hover_text = f"""
        <b style='font-size:14px'>{title}</b><br>
        <span style='font-family:monospace;font-size:11px'>{url[:80]}...</span><br><br>
        <b>🚨 Threat Level:</b> <span style='color:{color}'>{threat}</span><br>
        <b>🔗 Connections:</b> {incoming} in, {outgoing} out<br>
        <b>📊 Centrality:</b> {centrality:.3f}<br>
        <b>📄 Page Size:</b> {page_size:,} bytes<br>
        <b>🕒 Last Crawled:</b> {last_crawled}
        """
        hover_texts.append(hover_text.strip())
    
    # Create enhanced node trace
    node_trace = go.Scatter(
        x=x_nodes, 
        y=y_nodes,
        mode='markers+text',
        text=node_labels,
        textposition='middle center',
        textfont=dict(
            size=9,
            color='white',
            family='Arial, sans-serif'
        ),
        hoverinfo='text',
        hovertext=hover_texts,
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(
                width=2, 
                color='rgba(255, 255, 255, 0.8)'
            ),
            opacity=0.9,
            # Add glow effect
            sizemode='diameter'
        ),
        name='Nodes',
        showlegend=False
    )
    
    # Create figure with all traces
    fig = go.Figure(data=edge_traces + [node_trace])
    
    # Enhanced layout with dark theme
    fig.update_layout(
        title=dict(
            text="<b>🕸️ Darknet Link Map</b><br><sub>Interactive Network Visualization</sub>",
            x=0.5,
            font=dict(size=22, color='#e2e8f0', family='Arial, sans-serif')
        ),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=40, l=40, r=40, t=80),
        
        # Enhanced annotations
        annotations=[
            # Legend
            dict(
                text="<b>Legend:</b> Node size ∝ centrality • Color = threat level • Line thickness ∝ link frequency",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=-0.05,
                xanchor='center', yanchor='top',
                font=dict(size=11, color='rgba(226, 232, 240, 0.8)')
            ),
            
            # Threat level legend
            dict(
                text="🟢 LOW | 🟡 MEDIUM | 🔴 HIGH | 🔴 CRITICAL",
                showarrow=False,
                xref="paper", yref="paper", 
                x=1.0, y=1.0,
                xanchor='right', yanchor='top',
                font=dict(size=10, color='rgba(226, 232, 240, 0.7)')
            )
        ],
        
        # Dark theme styling
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False,
            range=[min(x_nodes) - 1, max(x_nodes) + 1] if x_nodes else [-1, 1]
        ),
        yaxis=dict(
            showgrid=False, 
            zeroline=False, 
            showticklabels=False,
            range=[min(y_nodes) - 1, max(y_nodes) + 1] if y_nodes else [-1, 1]
        ),
        
        plot_bgcolor='#0f172a',     # Dark slate background
        paper_bgcolor='#0f172a',    # Match plot background
        font=dict(color='#e2e8f0'), # Light text
        height=750,
        
        # Add subtle grid pattern
        shapes=[
            # Optional: Add subtle background pattern
        ]
    )
    
    return fig

def display_graph_tables(graph_data):
    """Display detailed node and edge information in tables"""
    
    tab1, tab2 = st.tabs(["📊 Top Nodes", "🔗 Recent Connections"])
    
    with tab1:
        if graph_data['nodes']:
            # Prepare nodes dataframe
            nodes_df = pd.DataFrame(graph_data['nodes'])
            
            # Select and rename columns for display
            display_columns = {
                'url': 'URL',
                'title': 'Title',
                'threat_level': 'Threat',
                'centrality_score': 'Centrality',
                'incoming_links': 'In Links',
                'outgoing_links': 'Out Links',
                'last_crawled': 'Last Crawled'
            }
            
            # Filter available columns
            available_cols = [col for col in display_columns.keys() if col in nodes_df.columns]
            display_df = nodes_df[available_cols].copy()
            display_df = display_df.rename(columns={k: v for k, v in display_columns.items() if k in available_cols})
            
            # Sort by centrality score
            if 'Centrality' in display_df.columns:
                display_df = display_df.sort_values('Centrality', ascending=False)
            
            # Truncate URLs and titles for display
            if 'URL' in display_df.columns:
                display_df['URL'] = display_df['URL'].str[:50] + '...'
            if 'Title' in display_df.columns:
                display_df['Title'] = display_df['Title'].str[:40] + '...'
            
            st.dataframe(
                display_df.head(20),
                use_container_width=True,
                hide_index=True
            )
    
    with tab2:
        if graph_data['edges']:
            # Prepare edges dataframe
            edges_df = pd.DataFrame(graph_data['edges'])
            
            # Select columns for display
            edge_columns = {
                'source_url': 'Source',
                'target_url': 'Target',
                'occurrence_count': 'Count',
                'last_seen': 'Last Seen',
                'is_external': 'External',
                'link_text': 'Link Text'
            }
            
            available_edge_cols = [col for col in edge_columns.keys() if col in edges_df.columns]
            edge_display_df = edges_df[available_edge_cols].copy()
            edge_display_df = edge_display_df.rename(columns={k: v for k, v in edge_columns.items() if k in available_edge_cols})
            
            # Sort by occurrence count
            if 'Count' in edge_display_df.columns:
                edge_display_df = edge_display_df.sort_values('Count', ascending=False)
            
            # Truncate URLs for display
            for col in ['Source', 'Target']:
                if col in edge_display_df.columns:
                    edge_display_df[col] = edge_display_df[col].str[:40] + '...'
            
            if 'Link Text' in edge_display_df.columns:
                edge_display_df['Link Text'] = edge_display_df['Link Text'].str[:30]
            
            st.dataframe(
                edge_display_df.head(20),
                use_container_width=True,
                hide_index=True
            )


def display_link_analytics():
    """Display link analytics and insights"""
    st.subheader("🔍 Link Analytics")
    
    try:
        stats = db_manager.get_link_map_statistics()
        
        # Top connected nodes
        if stats.get('top_nodes'):
            st.write("**🌟 Most Connected Sites:**")
            top_nodes_df = pd.DataFrame(stats['top_nodes'])
            
            for idx, node in top_nodes_df.head(5).iterrows():
                with st.expander(f"🔗 {node.get('title', 'No Title')[:50]}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**URL:** {node.get('url', '')[:60]}...")
                        st.write(f"**Threat Level:** {node.get('threat_level', 'Unknown')}")
                    with col2:
                        st.write(f"**Incoming Links:** {node.get('incoming_links', 0)}")
                        st.write(f"**Outgoing Links:** {node.get('outgoing_links', 0)}")
                        st.write(f"**Centrality Score:** {node.get('centrality_score', 0):.2f}")
        
        # Recent discoveries
        if stats.get('recent_nodes'):
            st.write("**🆕 Recently Discovered:**")
            recent_df = pd.DataFrame(stats['recent_nodes'])
            
            display_cols = ['url', 'title', 'threat_level', 'discovery_date']
            available_recent_cols = [col for col in display_cols if col in recent_df.columns]
            
            if available_recent_cols:
                recent_display = recent_df[available_recent_cols].head(10).copy()
                recent_display['url'] = recent_display['url'].str[:50] + '...'
                if 'title' in recent_display.columns:
                    recent_display['title'] = recent_display['title'].str[:40]
                
                st.dataframe(recent_display, use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.warning(f"Could not load link analytics: {e}")

if __name__ == "__main__":
    # For testing
    create_link_map_tab()
